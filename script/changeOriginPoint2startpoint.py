# -*- coding: utf-8 -*-
"""
Created on Sat Sep 11 17:20:06 2021

@author: 13113
"""

"""
Created on Sat Sep 11 16:08:18 2021

@author: 13113
"""
outputname = 'test123.txt'
#force,k,correct
import numpy as np
class changeOriginPoint2startpoint():
    def __init__(self,zpo,ljp,fc):
        self.zpo = zpo
        self.ljp = ljp
        self.fc = fc
    def run(self,index):
        self.fc.data = self.zpo[index]
        self.fc.recover_force(self.ljp)
        data = self.fc.get_prodata()['retract']
        data_x,data_y = data['measuredHeight'],data['vDeflection']
        x = data_x[np.argmin(data_y)]
        self.fc.data['offset']['x'] = self.fc.data['offset']['x']+x
        self.zpo.changingforce(self.fc)
    def end(self):
        self.zpo.changedforce()