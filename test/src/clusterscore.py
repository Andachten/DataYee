# -*- coding: utf-8 -*-
"""
Created on Tue Jun  1 09:09:11 2021

@author: ZhengBin
"""
from sklearn.neighbors import KernelDensity
import numpy as np
from scipy.signal import find_peaks
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
    return find_peaks(np.exp(log_dens)/np.exp(log_dens).max(),height=0.15,distance=5)
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
def wlc_dist(s1,s2):
    pass