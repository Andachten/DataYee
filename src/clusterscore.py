# -*- coding: utf-8 -*-
"""
Created on Tue Jun  1 09:09:11 2021

@author: ZhengBin
"""
from sklearn.neighbors import KernelDensity
import numpy as np
from src.loadjpk import forcecurve,loadjpkfile,zipfileopera
from dtaidistance import dtw
from src.datapro import wlc2lc,cal_baseline_x,cal_baseline_y
from scipy.spatial.distance import pdist,squareform
from sklearn.cluster import KMeans
def WLC_transformer(f,x,thre=30):
    x = x[np.where(f>thre)].astype(complex)*1e-9
    f = f[np.where(f>thre)].astype(complex)*1e-12
    p = np.array([0.36e-9],dtype=complex)
    lc = wlc2lc(x,f,p)
    return f,lc
def Lc_transformer(data_x,data_y,length=400,step=2,thre=30):
    f,x = WLC_transformer(data_y,data_x,thre=thre)
    x,f = x.real*1e9,f.real*1e12
    if len(x)<=10:
        return np.zeros(len(np.arange(0,length,step)))
    kde = KernelDensity(kernel='gaussian', bandwidth=2).fit(x.reshape(-1,1))
    x_ = np.arange(0,length,2)
    log_dens = kde.score_samples(x_.reshape(-1,1))
    return  np.exp(log_dens)
def count_0(x):
    x_ = np.array([])
    for i in x:
        if len(x_)==0:
            x_ = i.reshape(1,2)
        if i[0]>x_[:,0].max() and i[1]>x_[:,1].max():
            x_ = np.vstack((x_,i))
    return len(x_)

def wlc_dist(s1,s2,dlc_thre=5,f_thre=30):
    s1,s2 = np.delete(s1,np.where(s1==0)[0]),np.delete(s2,np.where(s2==0)[0])
    s1_dlc,s2_dlc = s1[:len(s1)//2],s2[:len(s1)//2]
    score = max(len(s1_dlc),len(s2_dlc))
    s1_ = np.tile(s1_dlc,(len(s2_dlc),1))
    s2_ = np.tile(s2_dlc.reshape(-1,1),(1,len(s1_dlc)))
    matrix_dlc = np.abs(s1_-s2_)
    arr_coor = np.dstack(np.where(matrix_dlc<=dlc_thre))[0]
    reduct = max(count_0(arr_coor),count_0(arr_coor[arr_coor[:,1].argsort()]))
    return 1-reduct/score

def distance(s1,s2):
    d = dtw.distance(s1,s2,window=int(0.25*len(s1)), penalty=0.2,use_c=True)
    return d
def get_distmatrix(zpo,ljp,length=400,step=2,thre=30,):
    import time
    t1 = time.time()
    fc = forcecurve()
    lst = []
    for i,data in enumerate(zpo):
        fc.data = data
        fc.recover_force(ljp)
        cal_baseline_y(fc)
        cal_baseline_x(fc)
        data = fc.get_prodata()['retract']
        data_x,data_y = data['measuredHeight']*1e9,data['vDeflection']*1e12
        res = Lc_transformer(data_x,data_y,length=length,step=step,thre=thre)
        if res.max()>0:
            lst.append(res/res.max())
        else:
            lst.append(res)
    arr = np.array(lst)
    t2=time.time()
    print("{}s".format(t2-t1))
    #dist =  pdist(arr,metric=distance)
    #matrix = squareform(dist)
    matrix = dtw.distance_matrix(arr,window=50,penalty=0.2,use_c=True,parallel=True)
    t3=time.time()
    print("{}s".format(t3-t2))
    return matrix
def sort_similar(index,matrix):
    arr = matrix[index,:]
    return arr.argsort()
def KMsClustering(matrix,n_clusters=8):
    km = KMeans(n_clusters=n_clusters,precompute_distance=True).fit(matrix)
    return km.labels_
    
        
if __name__=='__main__':
    pass
        
        
        