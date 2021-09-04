# -*- coding: utf-8 -*-
"""
Created on Sat Sep  4 15:44:37 2021

@author: 13113
"""
import numpy as np
class exportMaxForce():
    def __init__(self,zpo,ljp,fc):
        self.zpo = zpo
        self.ljp = ljp
        self.fc = fc
        self.arr = np.array([])
    def run(self,index):
        self.fc.data = self.zpo[index]
        self.fc.recover_force(self.ljp)
        data_y = self.fc.get_prodata(s=13)['retract']['measuredHeight']
        self.arr = np.append(self.arr,data_y.max())
    def end(self):
        np.savetxt(r'D:\code\py\DataYee\script/text.txt',self.arr)