# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 14:54:58 2021

@author: ZhengBin
"""
from src.datapro import cal_baseline,findpeak,findbottom,wlcfit,cleanpeak,countdlc,mkbaseondlc,predict,peaknumjudge,slope
func_lst = [cal_baseline,predict,findpeak,findbottom,wlcfit,cleanpeak,countdlc,mkbaseondlc,peaknumjudge,slope]
def process_customize(fc,functions=[0]):
    for i in functions:
        func_lst[i](fc)
def main(fc,zpo):
    if fc.data['rawdata'] == {}:
        return None
    process_customize(fc, [0, 2, 3, 4, 5, 6, 7, 8])
    if not fc.data['peaknum_judge']:
        return None
    process_customize(fc, [1])
    if not fc.data['mobilenet_judge']:
        return None
    zpo.changingforce(fc)
if __name__ == '__main__':
    import time,datetime
    t1 = time.time()
    #batch_fc_pro(r'D:\code\py\DataYeeN\20201125-COH-I30-I32-NGL-9GLINKER\20201125-COH-I30-I32-NGL-9GLINKER')
    t2 = time.time()
    print(str(datetime.timedelta(seconds=t2-t1)))