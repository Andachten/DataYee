# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from multiprocessing import Pool
class multi_run():
    def __init__(self,name):
        super().__init__()
        self.name=name
    def createPool(self,multi_n=4):
        self.multi_n=multi_n
        self.pool = Pool(self.multi_n)
    def inputTask(self,func,arglst):
        res = []
        for arg in arglst:
            res.append(self.pool.apply_async(func,(*arg,)))
        self.pool.close()
        self.pool.join()
        self.results =  [i.get() for i in res]
def splitRange(lens,n):
    if lens==1:
        return [range(0,1)]
    step = int(lens / n) + 1
    lst = []
    for i in range(0,lens,step):
        if i+step<lens:
            lst.append(range(i,i+step))
        else:
            lst.append(range(i,i+step-1))
    return lst
if __name__=='__main__':
    pass