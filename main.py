# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 14:54:58 2021

@author: ZhengBin
"""
from loadjpk import forcecurve,loadjpkfile,zipfileopera
from datapro import cal_baseline,findpeak,findbottom,wlcfit,cleanpeak,countdlc,mkbaseondlc,predict,peaknumjudge,slope
func_lst = [cal_baseline,predict,findpeak,findbottom,wlcfit,cleanpeak,countdlc,mkbaseondlc,peaknumjudge,slope]
def process_customize(fc,functions=[0]):
    for i in functions:
        func_lst[i](fc)
def del_index(fc,i_lst=[]):
    for i in i_lst[::-1]:
        del fc.data['peakindex'][i]
    process_customize(fc,list(range(3,8)))
def wlc_opera(fc,index=0,lclp=(0,0)):
    lc = fc.data['wlc'][index][0]
    lp = fc.data['wlc'][index][1]
    fc.data['wlc'][index] = (lc+lclp[0],lp+lclp[1])
    process_customize(fc,[7])
def batch_fc_pro(filedir = r'D:\code\py\DataYeeN\20210408-G2-I278-SPEED1\20210408-G2-I278-SPEED1'):
    datacollection = loadjpkfile(filedir)
    zip_opera = zipfileopera()
    fc = forcecurve()
    for i,data in enumerate(datacollection):
        fc.data = data
        process_customize(fc,list(range(len(func_lst))))
        zip_opera.addforce(fc)
        print('Num.{} total.{} has been done'.format(i, len(datacollection)))
if __name__ == '__main__':
    import time,datetime
    t1 = time.time()
    #batch_fc_pro(r'D:\code\py\DataYeeN\20201125-COH-I30-I32-NGL-9GLINKER\20201125-COH-I30-I32-NGL-9GLINKER')
    t2 = time.time()
    print(str(datetime.timedelta(seconds=t2-t1)))