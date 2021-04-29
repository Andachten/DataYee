# -*- coding: utf-8 -*-
"""
Created on Mon Apr 12 22:36:30 2021

@author: 13113
"""

from loadjpk import forcecurve,loadjpkfile
from datapro import feature_extract,cal_baseline
import time
import matplotlib.pyplot as plt
ljp = loadjpkfile(r'D:\code\py\DataYeeN\20210408-G2-I278-SPEED1')
n=0
for data in ljp:
    fc = forcecurve()
    fc.data = data
    cal_baseline(fc)
    data_y =fc.get_prodata()['retract']['vDeflection'][:,0]*1e12
    data_x = fc.get_prodata()['retract']['measuredHeight'][:,0]*1e9
    plt.plot(data_x,data_y)
    plt.ylim(-20,max(data_y))
    plt.xlim(-20,350)
    fig = feature_extract(data_y)
    plt.show()
    print('num.{} /total.{}'.format(n, len(ljp)))
    num = input("please input")
    n+=1
    plt.close()
    if num.isdigit() and int(num)<4:
        name = 'dataset/'+num+'/'+str(time.time()+n)+'.png'
        fig.savefig(name,bbox_inches='tight')
    else:
        continue