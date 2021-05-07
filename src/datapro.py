# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 09:16:35 2021

@author: ZhengBin
"""
import numpy as np
import copy
from scipy.signal import savgol_filter,find_peaks,medfilt
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import torchvision.transforms as transforms
import torch
from PIL import Image
import matplotlib as mpl
from numba import jit
mpl.rcParams['font.family']='Arial'
mpl.rcParams['axes.labelsize']=8
mpl.rcParams['axes.labelweight']='normal'
mpl.rcParams['axes.linewidth']=0.5
mpl.rcParams['font.size'] = 8
mpl.rcParams['axes.spines.right']=False
mpl.rcParams['axes.spines.top']=False
arg_run = {'peakH':50,
           'sens':10,
           'peakN':(2,8),
           'xlim':20,
           'lp':(0.34,0.38),
           'mark':{'GB1':(14,23),'MT':(1,14)},
           'fitjudge':False}
@jit(nopython=True)
def func(x,k,b):
    return k*x+b
@jit(nopython=True)
def lcfunc(x,lc,lp):
    return 1.3806e-23*298/(lp*1e-9)*(1/4*(1-x/lc)**(-2)+x/lc-1/4)*1e12
def loadmodel():
    global model,device,transform
    model = torch.load(r'./model/2021-04-26-01-mobilenet_v2-1.7.1-model.pkl', map_location='cpu')
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.eval()
    transform = transforms.Compose([transforms.Resize(224), transforms.ToTensor(), ])
def feature_extract(data_y):
    peakindex,_ = find_peaks(data_y, height = 25, prominence = 40, width = 30)
    #1st_D of vDeflection
    y_1d = -np.gradient(data_y)
    y_1d_bkup = y_1d
    #smooth 1st_D
    y_1d = medfilt(y_1d,9)
    y_1d_bkup[y_1d<5] = 0
    y_1d_bkup[y_1d_bkup<0] = 0
    arr = np.argwhere(y_1d_bkup>0).reshape(-1)
    #remove near peak of 1st_D
    lst1=[]
    lst2=[]
    for i in range(len(arr)):
        if i+1<len(arr) and arr[i] + 3  > arr[i+1]:
            lst2.append(arr[i])
        elif i ==len(arr):
            lst2.append(arr[i])
            lst1.append(lst2)
            lst2=[]
        else:
            lst2.append(arr[i])
            lst1.append(lst2)
            lst2=[]
    for i in lst1:
        lst2.append(int(np.mean(i)))
    for i in range(len(data_y)):
        if i not in peakindex:
            data_y[i]=0
    for i in range(len(y_1d_bkup)):
        if i not in lst2:
            y_1d_bkup[i]=0
    fig = plt.figure(figsize=(2.24,2.24))
    ax = fig.add_subplot(111)
    plt.axis('off')
    plt.subplots_adjust(top=1, bottom=0.1, right=1, left=0.1)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    #preparation of normolazation
    if np.max(y_1d_bkup)==0:
        a_max=1
    else:
        a_max=np.max(y_1d_bkup)
    if np.max(data_y)==0:
        y_max=1
    else:
        y_max=np.max(data_y)
    ax.plot(y_1d_bkup/a_max,color='#FF0000',linewidth=0.8)
    ax.plot(data_y/y_max*-1,'#0000FF',linewidth=0.8)
    plt.close()
    return fig
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
    plt.close()
    return fig
def fig2img(fig):
    fig.canvas.draw()
    img = Image.frombytes('RGB', fig.canvas.get_width_height(), fig.canvas.tostring_rgb())
    return img
def cal_baseline(forcecurve):
    data = copy.deepcopy(forcecurve.data['rawdata']['retract'])
    data['vDeflection'] = savgol_filter(data['vDeflection'][:,0],29,2).reshape(len(data['vDeflection']),1)
    xy_data = data[int(0.9*len(data['measuredHeight'])):]
    forcecurve.data['offset']['y'] = xy_data['vDeflection'].mean()
    data['vDeflection'] = data['vDeflection'] - forcecurve.data['offset']['y']
    for i,v in enumerate(data['vDeflection']):
        if v*data['vDeflection'][i+1]<0:
            forcecurve.data['offset']['x'] = 0.5*(data['measuredHeight'][i]+data['measuredHeight'][i+1])
            break
    #forcecurve.data['offset']['x'] = data['measuredHeight'][:,0][np.where(np.abs(data['vDeflection'][:,0])<1e-12)[0][0]]
    data['measuredHeight'] = data['measuredHeight'] - forcecurve.data['offset']['x']
loadmodel()

def predict(forcecurve,get_img=False):
    fig = feature(forcecurve)
    img = fig2img(fig)
    img = transform(img)
    img = img.unsqueeze(0)
    img = img.to(device)
    with torch.no_grad():
        py = model(img)
    pb=torch.nn.functional.softmax(py,dim=1)
    _, predicted = torch.max(pb,1)
    classIndex_ = predicted[0]
    if classIndex_.item()< 1:
        forcecurve.data['mobilenet_judge'] = True
    else:
        forcecurve.data['mobilenet_judge'] = False
    if get_img:
        return fig
#execute after calbaseline
def findpeak(forcecurve,height=arg_run['peakH'],sens=arg_run['sens'],xlim=arg_run['xlim']):
    forcecurve.data['peakindex']=[]
    data_y = forcecurve.get_prodata(tip_correc = False,s=55)['retract']['vDeflection'][:,0]*1e12
    p,_ = find_peaks(data_y,height=height,prominence=sens,width=6,distance=25)
    data = forcecurve.get_prodata(tip_correc = False)['retract']
    data_y = data['vDeflection'][:,0]*1e12
    data_x = data['measuredHeight'][:,0]*1e9
    p1,_ = find_peaks(data_y,height=height,prominence=sens,width=6,distance=25)
    peak_index = np.array([])
    for n in p:
        idx = (np.abs(p1-n)).argmin()
        if len(peak_index)!=0:
            temp = (p1[idx]-peak_index)
            if temp.min()<25:
                if data_y[temp.argmin()] > p1[idx]:
                    continue
                else:
                    peak_index = np.delete(peak_index,temp.argmin())
        peak_index = np.append(peak_index,p1[idx])
    peak_index = peak_index.astype(np.int)
    x_judge = data_x[peak_index]>xlim
    peak_index = peak_index[x_judge]
    forcecurve.data['peakindex']=peak_index
    return peak_index
#must execute after findpeak
def findbottom(forcecurve):
    forcecurve.data['bottomindex']=[]
    peak_index = forcecurve.data['peakindex']
    data = forcecurve.get_prodata()['retract']
    data_y = data['vDeflection'][:,0]*1e12
    data_x = data['measuredHeight'][:,0]*1e9
    for i,p_i in enumerate(peak_index):
        if i==0:
            temp = p_i
            while True:
                k = curve_fit(func, data_x[temp-50:temp], data_y[temp-50:temp])[0][0]
                if k<0.01 or data_x[temp]<10:
                    if temp == p_i:
                        temp-=10
                    forcecurve.data['bottomindex'].append(temp)
                    break
                else:
                    temp-=50
        else:
            temp = peak_index[i-1]+np.argmin(data_y[peak_index[i-1]:peak_index[i]])
            forcecurve.data['bottomindex'].append(temp)
#must execute after findbottom
def wlcfit(forcecurve,lp = arg_run['lp']):
    forcecurve.data['wlcarg'] = []
    data = forcecurve.get_prodata()['retract']
    data_y = data['vDeflection'][:,0]*1e12
    data_x = data['measuredHeight'][:,0]*1e9
    peak_index = forcecurve.data['peakindex']
    bottom_index = forcecurve.data['bottomindex']
    boundary_force = 150#doi: 10.3389/fmolb.2020.00085
    for i in range(len(peak_index)):
        p_i = peak_index[i]
        b_i = bottom_index[i]
        if data_y[p_i]>boundary_force:
            y_distance = data_y[p_i]-data_y[b_i]
            y_fitpoint = data_y[b_i]+0.3*y_distance
            if len(np.where(data_y[b_i:]>y_fitpoint)[0])!=0:
                fitpoint = np.where(data_y[b_i:]>y_fitpoint)[0][0]+b_i
            else:
                x_distance = data_x[p_i]-data_x[b_i]
                x_fitpoint = data_x[b_i]+0.4*x_distance
                fitpoint = np.where(data_x[b_i:]>x_fitpoint)[0][0]+b_i
            if len(data_x[b_i:fitpoint])<50:
                fitpoint = p_i
            try:
                popt,_ = curve_fit(lcfunc, data_x[b_i:fitpoint], data_y[b_i:fitpoint], bounds=([data_x[p_i],lp[0]],[data_x[p_i]+50,lp[1]]))
            except:
                popt=(0,0)
                #print(err)
        else:
            try:
                popt,_ = curve_fit(lcfunc, data_x[b_i:p_i], data_y[b_i:p_i], bounds=([data_x[p_i],lp[0]],[data_x[p_i]+50,lp[1]]))
            except:
                popt=(0,0)
        lc,p=popt
        forcecurve.data['wlcarg'].append((lc,p))
def cleanpeak(forcecurve):
    peak_index = forcecurve.data['peakindex']
    bottom_index = forcecurve.data['bottomindex']
    wlcarg = forcecurve.data['wlcarg']
    accept_lst = []
    for i in range(len(wlcarg)):
        if sum(wlcarg[i])!=0:
            accept_lst.append(i)
    if len(accept_lst) != 0:
           forcecurve.data['peakindex'] = []
           forcecurve.data['bottomindex'] = []
           forcecurve.data['wlcarg'] = []
           for i in accept_lst:
               forcecurve.data['peakindex'].append(peak_index[i])
               forcecurve.data['bottomindex'].append(bottom_index[i])
               forcecurve.data['wlcarg'].append(wlcarg[i])
#must execute after wlcfit and cleanpeak
def countdlc(fc):
    fc.data['dlc'] = []
    wlcarg = fc.data['wlcarg']
    for i in range(len(wlcarg)):
        if i!=len(wlcarg)-1:
            fc.data['dlc'].append(wlcarg[i+1][0]-wlcarg[i][0])
def mkbaseondlc(fc,dic=arg_run['mark']):
    fc.data['mark'] = []
    dlc = fc.data['dlc']
    for i in range(len(dlc)):
        for m,rang in dic.items():
            if dlc[i]>rang[0] and dlc[i]<rang[1]:
                fc.data['mark'].append(m)
        if len(fc.data['mark'])-1!=i:
            fc.data['mark'].append('none')
def peaknumjudge(fc,peakN=arg_run['peakN']):
    peaknum = len(fc.data['peakindex']  )
    if peaknum > peakN[0] and peaknum<peakN[1]:
        fc.data['peaknum_judge'] = True
    else:
        fc.data['peaknum_judge'] = False
def slope(fc):
    fc.data['k'] = []
    peak_index = fc.data['peakindex']
    bottom_index = fc.data['bottomindex']
    data = fc.get_prodata()['retract']
    data_y = data['vDeflection'][:,0]*1e12
    data_x = data['measuredHeight'][:,0]*1e9
    for i in range(len(peak_index)):
        x,y = data_x[bottom_index[i]:peak_index[i]],data_y[bottom_index[i]:peak_index[i]]
        if len(x)>150:
            deg = 5
        else:
            deg = 1
        re = np.polyfit(x,y,deg)

        d = np.polyder(re)
        k = np.polyval(d,data_x[peak_index[i]])
        b = data_y[peak_index[i]]-k*data_x[peak_index[i]]
        fc.data['k'].append((k,b))
        
def graph(forcecurve):
    fig,ax = plt.subplots(dpi=300,figsize=(8,5))
    data = forcecurve.get_prodata()['retract']
    data_y = data['vDeflection'][:,0]*1e12
    data_x = data['measuredHeight'][:,0]*1e9
    peak_index = forcecurve.data['peakindex']
    bottom_index = forcecurve.data['bottomindex']
    ax.plot([-5,5],[0,0],'r-',lw=1)
    ax.plot([0,0],[-50,50],'r-',lw=1)
    ax.set_xlim([-5,data_x[peak_index[-1]]+40])
    ax.set_ylim([-30,data_y.max()+40])
    ax.set_yticks(np.arange(0,data_y.max(),150))
    ax.plot(data_x,data_y,'k',lw=0.5)
    ax.plot(data_x[peak_index],data_y[peak_index],'ro',markersize=2)
    ax.plot(data_x[bottom_index],data_y[bottom_index],'g*',markersize=7)
    for i in range(len(forcecurve.data['wlcarg'])):
        wlcarg = forcecurve.data['wlcarg'][i]
        if sum(wlcarg)==0:
            continue
        x_ = np.linspace(0,data_x[peak_index[i]]+10)
        y_ = lcfunc(x_,*wlcarg)
        ax.plot(x_,y_,'-.',lw=0.5)
    for i in range(len(forcecurve.data['k'])):
        x_ = np.linspace(data_x[peak_index[i]]-10,data_x[peak_index[i]]+5)
        y_ = forcecurve.data['k'][i][0]*x_+forcecurve.data['k'][i][1]
        ax.plot(x_,y_,'b-.')
    return fig,ax