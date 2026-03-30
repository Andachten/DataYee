# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 09:06:46 2022

@author: zbin
"""
import numpy as np
class sortByClass():
    def __init__(self,zpo,ljp,fc):
        self.zpo = zpo
        self.ljp = ljp
        self.fc = fc
        self.lst = []
    def run(self,index):
        self.fc.data = self.zpo[index]
        self.lst.append(ord(self.fc.data['class']))
        self.fc.data['filters']['win_lens']=13
        self.zpo.changingforce(self.fc)
        print(index)
    def end(self):
        self.lst = np.array(self.lst).reshape(-1)
        i = np.argsort(self.lst)
        self.zpo.resortForce(i)
        self.zpo.changedforce(save=False)
        pass