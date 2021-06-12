# -*- coding: utf-8 -*-
"""
Created on Tue Jun  1 09:09:11 2021

@author: ZhengBin
"""
from sklearn.neighbors import KernelDensity
import numpy as np
from scipy.signal import find_peaks
from tslearn.metrics import cdist_dtw
from tslearn.preprocessing import TimeSeriesScalerMeanVariance,TimeSeriesResampler
from loadjpk import forcecurve,loadjpkfile,zipfileopera
from numba import njit
from scipy.ndimage import gaussian_filter
from scipy.signal import savgol_filter
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
    for i, v in enumerate(data_y):
        if v * data_y[i + 1] < 0:
            fc.data['offset']['x'] = 0.5 * (data_x[i] + data_x[i + 1])
            break
        if i>int(0.5*len(data_x)):
            fc.data['offset']['x'] = data_x[0]
            break
def WRC_transformer(f,x,thr=20):
    b,gama = 0.11e-9,41/180*np.pi
    kb = 1.38e-23
    T = 298
    x = x[np.where(f>thr)]*1e-9
    f = f[np.where(f>thr)]*1e-12
    l=b*np.cos(gama/2)/np.abs(np.log(np.cos(gama)))
    f_b = kb*T*l/b**2
    x1 = x[np.where(f<f_b)]/(1-(4*f[np.where(f<f_b)]*l/kb/T)**(-0.5))
    x2 = x[np.where(f>=f_b)]/(1-(2*f[np.where(f>=f_b)]*b/kb/T)**(-1))
    return np.hstack((f[np.where(f<f_b)],f[np.where(f>=f_b)]))*1e12,np.hstack((x1,x2))*1e9
def Lc_transformer(data_x,data_y,plottype='hist'):
    f,x = WRC_transformer(data_y,data_x)
    sort = np.argsort(x)
    x,f = x[sort],f[sort]
    kde = KernelDensity(kernel='gaussian', bandwidth=2).fit(x.reshape(-1,1))
    x_ = np.arange(int(x.min()),int(x.max()))
    log_dens = kde.score_samples(x_.reshape(-1,1))
    p,_ = find_peaks(np.exp(log_dens)/np.exp(log_dens).max(),height=0.15,distance=5,prominence=0.1)
    lc = x_[p]
    dlc = np.diff(lc,prepend=0)
    f_max = np.array([])
    for i,_ in enumerate(lc):
        if i!=len(lc)-1:
            index = np.where((lc[i]<x_)&(lc[i+1]>x_))[0]
        else:
            index = np.where(lc[i]<x_)[0]
        f_max = np.append(f_max,f[index].max())
    return dlc,f_max

#@njit
def count_0(x):
    x_ = np.array([])
    for i in x:
        if len(x_)==0:
            x_ = i.reshape(1,2)
        if i[0]>x_[:,0].max() and i[1]>x_[:,1].max():
            x_ = np.vstack((x_,i))
    return len(x_)

def wlc_dist(s1,s2,dlc_thre=5,f_thre=30):
    s1,s2 = np.delete(s1,np.where(s1==0)[0]),np.delete(s2,np.where(s2==0)[0])
    s1_dlc,s2_dlc = s1[:len(s1)//2],s2[:len(s1)//2]
    score = max(len(s1_dlc),len(s2_dlc))
    s1_ = np.tile(s1_dlc,(len(s2_dlc),1))
    s2_ = np.tile(s2_dlc.reshape(-1,1),(1,len(s1_dlc)))
    matrix_dlc = np.abs(s1_-s2_)
    arr_coor = np.dstack(np.where(matrix_dlc<=dlc_thre))[0]
    reduct = max(count_0(arr_coor),count_0(arr_coor[arr_coor[:,1].argsort()]))
    return 1-reduct/score
if __name__=='__main__':
    ljp = loadjpkfile(r'D:\jpkdata\20201201-COH-(I29)3-NGL-0_4UMS')
    fc = forcecurve()
    arr = np.array([])
    for i,data in enumerate(ljp):
        fc.data = data
        noise_down(fc)
        cal_baseline_y(fc)
        cal_baseline_x(fc)
        data = fc.get_prodata()['retract']
        data_x,data_y = data['measuredHeight'].reshape(-1)*1e9,data['vDeflection'].reshape(-1)*1e12
        data_y = TimeSeriesResampler(sz=100).fit_transform(data_y).reshape(-1)
        p,_ = find_peaks(data_y,height=20,prominence=5)
        data_y[np.delete(np.arange(len(data_y)),p)] = 0
        data_y/=data_y.max()
        if len(arr)==0:
            arr = np.array([data_y])
        else:
            arr = np.vstack((arr,np.array([data_y])))

        