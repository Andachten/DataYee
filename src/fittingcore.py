# -*- coding: utf-8 -*-
"""
Created on Tue Jun  8 18:15:07 2021

@author: ZhengBin
"""
import numpy as np
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
def fit(x_arr,y_arr,bounds,methods='BE',scale_factor=0.5):
    while True:
        inputs = list(product(*[np.linspace(x,y) for x,y in bounds]))
        if methods=='BE':
            y_pre = BE(x_arr,*)
            pass
        elif methods == 'DHS':
            pass
        elif methods == 'FD':
            pass
