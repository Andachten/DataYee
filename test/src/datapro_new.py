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
def noise_down(fc):
    data_y = fc.data['rawdata']['retract']['vDeflection'] * 1e12
    r = 0.9
    data_y_right = data_y[:, 0][int(r * len(data_y)):]
    data_y_right_smth = gaussian_filter(data_y_right, 11)
    for s in np.arange(30)[3::2]:
        err = np.abs(savgol_filter(data_y[:, 0][int(r * len(data_y)):], s, 2) - data_y_right_smth).mean()
        if err < 4:
            break
    fc.data['filters']['win_lens'] = s
def cal_baseline_drift(fc):
    fc.data['offset']['k'] = 0
    data = fc.get_prodata()['retract']
    data_x,data_y = data['measuredHeight']*1e9,data['vDeflection']*1e12
    if len(fc.data['peakindex'])==0:
        index = int(len(data_x)*0.9)
        p = np.polyfit(data_x[index:].reshape(-1), data_y[index:].reshape(-1), 1)
        d = np.polyder(p)
        k = np.polyval(d, data_x.reshape(-1)[-1])
    else:
        pass
    fc.data['offset']['k'] = k
def cal_baseline_y(fc):
    fc.data['offset']['y'] = 0
    data = fc.get_prodata()['retract']
    data_y = data['vDeflection']
    index = int(len(data_y)*0.9)
    fc.data['offset']['y'] = data_y[index:].mean()
    
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
    pass
def wlcfit(fc):
    pass
def peakN_judge(fc):
    pass
def slope(fc):
    pass

