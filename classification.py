# -*- coding: utf-8 -*-
"""
Created on Sun Apr 25 09:04:16 2021

@author: 13113
"""
import os
from loadjpk import loadjpkfile,forcecurve
from datapro import cal_baseline,findpeak
from scipy.signal import find_peaks
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import random
def fig2img(fig):
    fig.canvas.draw()
    img = Image.frombytes('RGB', fig.canvas.get_width_height(), fig.canvas.tostring_rgb())
    return img
def feature(fc):
    data_y = fc.get_prodata(tip_correc=False,s=53)['retract']['vDeflection'][:,0]*1e12
    peakindex,_ = find_peaks(data_y,height=30,prominence=14,width=14,distance=50)
    
    d = fc.get_prodata(tip_correc=False,s=13)['retract']['vDeflection'][:,0]*1e12
    d = d/d.max()
    d1 = np.gradient(data_y)
    d1 = d1/d1.max()
    d1_peakindex,_ = find_peaks(d1,height=0.15,distance=100)
    if len(d1_peakindex)>len(peakindex):
        d1_peakindex = d1_peakindex[d1[d1_peakindex].argsort()[::-1]][:len(peakindex)]
    for i,_ in enumerate(d):
        if i not in peakindex:
            d[i]=0
    for i,_ in enumerate(d1):
        if i not in d1_peakindex:
            d1[i]=0
    fig,ax = plt.subplots(figsize=(2.24,2.24))
    plt.axis('off')
    plt.subplots_adjust(top=1, bottom=0.1, right=1, left=0.1)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    ax.plot(d,color='#FF0000',linewidth=1,alpha=0.9)
    ax.plot(d1*-1,'#0000FF',linewidth=1,alpha=0.9)
    return fig
def savefig(fig,clas,spath,fname):
    if not os.path.isdir(spath):
        os.mkdir(spath)
    savepath = os.path.join(spath,str(clas))
    if not os.path.isdir(savepath):
        os.mkdir(savepath)
    img = fig2img(fig)
    img = img.resize((224,224))
    img.save(os.path.join(savepath,fname))
def plotcurve(fc):
    data_x = fc.get_prodata(tip_correc = False)['retract']['measuredHeight'][:,0]*1e9
    data_y = fc.get_prodata(tip_correc=False)['retract']['vDeflection'][:,0]*1e12
    findpeak(fc)
    fig,ax = plt.subplots()
    if len(fc.data['peakindex'])>0:
        ax.set_xlim((-5,data_x[fc.data['peakindex'][-1]]+20))
    else:
        ax.set_xlim((-5,data_x.max()+10))
    ax.set_ylim((-40,data_y.max()+10))
    ax.plot(data_x,data_y,'k')
    plt.show()
    plt.close()
if __name__ == '__main__':
    path = r'D:\code\py\DataYeeN\jpkfile'
    ljp = loadjpkfile(path)
    seq  = [i for i in range(len(ljp))]
    seq_r = random.sample(seq,len(ljp))
    fc = forcecurve()
    for i in seq_r:
        fc.data = ljp[i]
        cal_baseline(fc)
        plotcurve(fc)
        if len(fc.data['peakindex'])>1:
            continue
        n = input('Plase enter class: ')
        if n.isdigit():
            fname = "{:0>4d}.jpg".format(seq_r[i])
            clas = n
            fig = feature(fc)
            spath = '20210425data'
            savefig(fig,clas,spath,fname)
            plt.close()
        elif n == 'E' or n =='e':
            break
        else:
            continue
    
    