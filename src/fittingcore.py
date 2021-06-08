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
def Friddle():
    pass
def DHS(x_arr,x_beta,k_off,dG):
    Feq = np.sqrt(2*k_off*dG)
    f_beta = kb*T/x_beta
    F_arr = Feq+f_beta*(1+np.e*(-gama)*x_arr/k_off/Feq/f_beta)
    pass
