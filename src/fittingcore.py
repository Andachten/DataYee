# -*- coding: utf-8 -*-
"""
Created on Tue Jun  8 18:15:07 2021

@author: ZhengBin
"""
import numpy as np
from itertools import product
T = 298
kb = 1.38e-23
gama = 0.577216
def BE(x_arr,x_beta,k_off):
    f_beta = kb*T/x_beta
    F_arr = f_beta*np.log(x_arr/f_beta/k_off)
    return F_arr
def Friddle(x_arr,x_beta,k_off,Feq):
    f_beta = kb*T/x_beta
    F_arr = Feq + f_beta*np.log(1+np.e**(-1*gama)*x_arr/(k_off*f_beta))
    return F_arr
def DHS(x_arr,x_beta,k_off,dG):
    pass
def r2_calculate(y_actual: np.ndarray,y_predicted: np.ndarray)->np.float64:
    sse = np.sum((y_actual - y_predicted) ** 2,axis=1)
    sst = np.sum((y_actual - np.mean(y_actual)) ** 2,axis=1)
    r2 = 1 - sse / sst
    return r2
def fit(x_arr,y_arr,bounds,methods='BE',scale_factor=0.3,max_iter=5):
    if methods == 'BE':
        arg_num = 2
        if len(bounds)!=arg_num:
            return False
        func = BE
    elif methods == 'Friddle':
        arg_num = 3
        if len(bounds)!=arg_num:
            return False
        func = Friddle
    elif methods == 'DHS':
        func = DHS
    max_r2 = 0
    best_arg = np.array([])
    for i in range(max_iter):
        b = np.array(list(product(*[np.linspace(x,y) for x,y in bounds]))).T
        arg = [np.tile(x.reshape(-1,1),(1,len(x_arr))) for x in b]
        res = func(x_arr,*arg)
        r2 = r2_calculate(res,y_arr)
        if max_r2 < r2.max(axis=0):
            max_r2 = r2.max(axis=0)
            max_r2_index = r2.argmax(axis=0)
            best_arg = b.T[max_r2_index]
            bounds = np.tile(best_arg.reshape(-1,1),(1,2))+np.tile(np.diff(bounds)*scale_factor,(1,2))*np.array([-1,1])
            bounds[np.where(bounds<0)]=1e-13
        else:
            break
    return max_r2,best_arg
    