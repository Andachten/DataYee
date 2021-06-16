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

if __name__=='__main__':
    pass