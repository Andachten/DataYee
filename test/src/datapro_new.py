# -*- coding: utf-8 -*-
"""
Created on Thu May 27 22:51:44 2021

@author: ZhengBin
"""
import numpy as np
import copy
from scipy.signal import savgol_filter, find_peaks, medfilt
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt
import torchvision.transforms as transforms
import torch
from PIL import Image
import matplotlib as mpl
from sklearn.neighbors import KernelDensity
mpl.rcParams['font.family'] = 'Arial'
mpl.rcParams['axes.labelsize'] = 8
mpl.rcParams['axes.labelweight'] = 'normal'
mpl.rcParams['axes.linewidth'] = 0.5
mpl.rcParams['font.size'] = 8
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.spines.top'] = False
def lcfunc(x, lc, lp):
    return 1.3806e-23 * 298 / (lp * 1e-9) * (1 / 4 * (1 - x / lc) ** (-2) + x / lc - 1 / 4) * 1e12
def rotate(data_x, data_y, index, k):
    theta = np.arctan(k) * -1
    return (data_x - data_x[index]) * np.sin(theta) + (data_y - data_y[index]) * np.cos(theta) + data_y[index]
def get_slope(x_arr,y_arr,index=-1):
    p = np.polyfit(x_arr,y_arr,1)
    d = np.polyder(p)
    k = np.polyval(d, x_arr[index])
    return k
def noise_down(fc):
    data_y = fc.data['rawdata']['retract']['vDeflection'] * 1e12
    r = 0.9
    data_y_right = data_y[:, 0][int(r * len(data_y)):]
    data_y_right_smth = gaussian_filter(data_y_right, 21)
    for s in np.arange(30)[3::2]:
        err = np.abs(savgol_filter(data_y[:, 0][int(r * len(data_y)):], s, 2) - data_y_right_smth).mean()
        if err < 4:
            break
    fc.data['filters']['win_lens'] = s
def cal_baseline_drift(fc):
    fc.data['offset']['k'] = 0
    data = fc.get_prodata()['retract']
    data_x,data_y = data['measuredHeight'],data['vDeflection']
    if len(fc.data['peakindex'])==0:
        index = int(len(data_x)*0.9)
        k = get_slope(data_x[index:].reshape(-1), data_y[index:].reshape(-1))
    else:
        pass
    fc.data['offset']['k'] = k
def cal_baseline_y(fc):
    fc.data['offset']['y'] = 0
    data = fc.get_prodata()['retract']
    data_y = data['vDeflection']
    index = int(len(data_y)*0.9)
    fc.data['offset']['y'] = data_y[index:].mean()*-1
    
def cal_baseline_x(fc):
    fc.data['offset']['x'] = 0
    data = fc.get_prodata()['retract']
    data_x,data_y = data['measuredHeight'],data['vDeflection']
    data_y = data_y - fc.data['offset']['y']
    for i, v in enumerate(data_y):
        if v * data_y[i + 1] < 0:
            fc.data['offset']['x'] = 0.5 * (data_x[i] + data_x[i + 1])
            break
def cal_highspeed_drift(fc):
    fc.data['offset']['highspeed'] = 0
    if not fc.data['arg']['highspeed']:
        return None
    data = fc.get_prodata()['retract']
    data_retract_y,data_extend_y = data['retract']['vDeflection'],data['extend']['vDeflection']
    data_retract_x,data_extend_x = data['retract']['measuredHeight'],data['extend']['measuredHeight']
    retract_index,extend_index = int(0.9*len(data_retract_y)),int(0.1*len(data_extend_y))
    if data_extend_x[0] > data_retract_x[retract_index]:
        corr = data_extend_y[:extend_index].mean()-data_retract_y[retract_index:].mean()
    else:
        corr = 0
    fc.data['offset']['highspeed'] = 0.5*corr
    pass
def findpeak(fc):
    fc.data['peakindex'] = np.array([])
    data = fc.get_prodata()['retract']
    data_x,data_y = data['measuredHeight']*1e9,data['vDeflection']*1e12
    d = np.gradient(np.gradient(gaussian_filter(data_y[:, 0], 29)))
    #extract noise index
    index_noise = int(len(d)*0.9)
    noise = np.abs(d[index_noise:]).max()*1.5
    #xlim index
    index_xlim = np.where(data_x>fc.data['arg']['xlim'])[0][0]
    d = d[index_xlim:]
    distance = len(data_x) - np.where(data_x<data_x[-1]-fc.data['arg']['xsens'])[0][-1]
    p = find_peaks(d*-1,height=noise,distance=distance)[0]+index_xlim
    b = find_peaks(d,height=noise,distance=distance)[0]+index_xlim
    for p_i in p:
        temp_array = data_x[b] - data_x[p_i]
        i = np.where(temp_array > 0, temp_array, np.inf)
        if len(i)==0:
            continue
        b_i = b[i.argmin()]
        if True:
            y = rotate(data_x[p_i - distance:b_i], data_y[p_i - distance:b_i], distance, -0.07)
            p_i = p_i - distance + np.argmax(y)
            k = np.polyval(np.polyder(np.polyfit(data_x[b_i:b_i + 300][:, 0], data_y[b_i:b_i + 300][:, 0], 1)), data_x[b_i])
            y = rotate(data_x[p_i:b_i + distance], data_y[p_i:b_i + distance], b_i - p_i, k - 0.07)
            b_i = p_i + np.argmin(y)
            fsens = data_y[p_i]-data_y[b_i]
            if fsens > fc.data['arg']['sens']:
                fc.data['peakindex'] = np.append(fc.data['peakindex'],p_i)
                fc.data['bottomindex'] = np.append(fc.data['bottomindex'],b_i)
    fc.data['peakindex'] = fc.data['peakindex'].astype(np.uint16)
    fc.data['bottomindex'] = fc.data['bottomindex'].astype(np.uint16)
    pass
def wlcfit(fc):
    fc.data['wlcarg'] = []
    n = 50
    data = fc.get_prodata()['retract']
    data_x,data_y = data['measuredHeight'].reshape(-1)*1e9,data['vDeflection'].reshape(-1)*1e12
    lp=fc.data['arg']['lp']
    for p_i in fc.data['peakindex']:
        temp = p_i
        while True:
            k = get_slope(data_x[temp - n:temp], data_y[temp - n:temp])
            if k < 0.01 or data_x[temp] < 10:
                if temp == p_i:
                    temp -= 10
                b_i = temp
                break
            else:
                temp -= n
        dy = (data_y[p_i]-data_y[b_i])*0.5
        fitpoint = np.where(data_x>data_y[b_i]+dy)[0][0]
        if p_i<=fitpoint:
            popt = (data_x[p_i],0.36)
            lc, p = popt
            fc.data['wlcarg'].append((lc, p))
            continue
        try:
            popt, _ = curve_fit(lcfunc, data_x[b_i:fitpoint], data_y[b_i:fitpoint],
                                    bounds=([data_x[p_i], lp[0]], [data_x[p_i] + 50, lp[1]]))
        except:
            popt = (data_x[p_i],0.36)
        lc, p = popt
        fc.data['wlcarg'].append((lc, p))
def peakN_judge(fc):
    pass
def slope(fc):
    pass

