 # -*- coding: utf-8 -*-
"""
Created on Thu May 27 22:51:44 2021

@author: ZhengBin
"""
import numpy as np
import copy
from scipy.signal import savgol_filter, find_peaks
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt
from PIL import Image
from src.predictcore import feature_extract,MobileNet
import matplotlib as mpl
from sklearn.neighbors import KernelDensity
mpl.rcParams['font.family'] = 'Arial'
mpl.rcParams['axes.labelsize'] = 8
mpl.rcParams['axes.labelweight'] = 'normal'
mpl.rcParams['axes.linewidth'] = 0.5
mpl.rcParams['font.size'] = 8
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.spines.top'] = False
m = MobileNet()
def lcfunc(x, lc, lp):
    return 1.3806e-23 * 298 / (lp * 1e-9) * (1 / 4 * (1 - x / lc) ** (-2) + x / lc - 1 / 4) * 1e12
def wlc2lc(x,f,lp):
    kb = 1.3806e-23
    T = 298
    lc = (4*f*lp*x+3*kb*T*x)/(6*f*lp)-(-16*f**2*lp**2*x**2+12*f*kb*lp*T*x**2-36*kb**2*T**2*x**2)/(12*2**(2/3)*f*lp*(-16*f**3*lp**3*x**3+72*f**2*kb*lp**2*T*x**3-27*f*kb**2*lp*T**2*x**3+54*kb**3*T**3*x**3+3*(3)**0.5*(-64*f**5*kb*lp**5*T*x**6+144*f**4*kb**2*lp**4*T**2*x**6-108*f**3*kb**3*lp**3*T**3*x**6+135*f**2*kb**4*lp**2*T**4*x**6)**0.5)**(1/3))+(-16*f**3*lp**3*x**3+72*f**2*kb*lp**2*T*x**3-27*f*kb**2*lp*T**2*x**3+54*kb**3*T**3*x**3+3*(3)**0.5*(-64*f**5*kb*lp**5*T*x**6+144*f**4*kb**2*lp**4*T**2*x**6-108*f**3*kb**3*lp**3*T**3*x**6+135*f**2*kb**4*lp**2*T**4*x**6)**0.5)**(1/3)/(6*2**(1/3)*f*lp)
    return lc
def lcfunc1d(x,lc,lp):
    return 4.114188*(1/lc + 0.5/(lc*(1 - x/lc)**3))/lp
def rotate(data_x, data_y, index, k):
    theta = np.arctan(k) * -1
    return (data_x - data_x[index]) * np.sin(theta) + (data_y - data_y[index]) * np.cos(theta) + data_y[index]
def get_slope(x_arr,y_arr,index=-1):
    p = np.polyfit(x_arr,y_arr,1)
    d = np.polyder(p)
    k = np.polyval(d, x_arr[index])
    return k
def fig2img(fig):
    fig.canvas.draw()
    img = Image.frombytes('RGB', fig.canvas.get_width_height(), fig.canvas.tostring_rgb())
    return img
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
 
    return False
def noise_down(fc):
    data_y = fc.data['rawdata']['retract']['vDeflection'] * 1e12
    r = 0.9
    data_y_right = data_y[:, 0][int(r * len(data_y)):]
    data_y_right_smth = gaussian_filter(data_y_right, 21)
    for s in np.arange(30)[3::2]:
        err = np.abs(savgol_filter(data_y[:, 0][int(r * len(data_y)):], s, 2) - data_y_right_smth).mean()
        if err < 4:
            break
    fc.data['filters']['win_lens'] = s
def cal_baseline_drift(fc):
    fc.data['offset']['k'] = 0
    data = fc.get_prodata()['retract']
    data_x,data_y = data['measuredHeight'],data['vDeflection']
    if len(fc.data['peakindex'])==0:
        index = int(len(data_x)*0.9)
        k = get_slope(data_x[index:].reshape(-1), data_y[index:].reshape(-1))
    else:
        k=0
    fc.data['offset']['k'] = k
def cal_baseline_y(fc):
    fc.data['offset']['y'] = 0
    data = fc.get_prodata()['retract']
    data_y = data['vDeflection']
    index = int(len(data_y)*0.9)
    fc.data['offset']['y'] = data_y[index:].mean()*-1
    
def cal_baseline_x(fc):
    fc.data['offset']['x'] = 0
    data = fc.get_prodata()['retract']
    data_x,data_y = data['measuredHeight'],data['vDeflection']
    for i, v in enumerate(data_y):
        if v * data_y[i + 1] < 0:
            fc.data['offset']['x'] = 0.5 * (data_x[i] + data_x[i + 1])
            break
        if i>int(0.5*len(data_x)):
            fc.data['offset']['x'] = data_x[0]
            break
def cal_highspeed_drift(fc):
    fc.data['offset']['highspeed'] = 0
    if not fc.data['arg']['highspeed']:
        return None
    data = fc.get_prodata()
    data_retract_y,data_extend_y = data['retract']['vDeflection'],data['extend']['vDeflection']
    data_retract_x,data_extend_x = data['retract']['measuredHeight'],data['extend']['measuredHeight']
    retract_index,extend_index = int(0.9*len(data_retract_y)),int(0.1*len(data_extend_y))
    if data_extend_x[0] > data_retract_x[retract_index]:
        corr = data_extend_y[:extend_index].mean()-data_retract_y[retract_index:].mean()
    else:
        corr = 0
    if corr>40e-12 or corr<0:
        return None
    fc.data['offset']['highspeed'] = 0.5*corr
    pass
def predict(fc):
    fig = feature_extract(fc)
    img = fig2img(fig)
    score = m.predict(img)
    if fc.data['arg']['modelstrict']:
        v = 1
    else:
        v = 2
    if score<=v:
        fc.data['mobilenet_judge']=True
    else:
        fc.data['mobilenet_judge']=False
def findpeak(fc):
    fc.data['peakindex'] = np.array([])
    fc.data['bottomindex'] = np.array([])
    data = fc.get_prodata(tip_correc=False)['retract']
    data_x,data_y = data['measuredHeight']*1e9,data['vDeflection']*1e12
    d = np.gradient(np.gradient(gaussian_filter(data_y[:, 0], 13)))
    #extract noise index
    index_noise = int(len(d)*0.9)
    noise = np.abs(d[index_noise:]).max()*1.1
    #xlim index
    index_xlim = np.where(data_x>fc.data['arg']['xlim'])[0][0]
    d = d[index_xlim:]
    distance = len(data_x) - np.where(data_x<data_x[-1]-fc.data['arg']['xsens'])[0][-1]
    p = find_peaks(d*-1,height=noise,distance=distance)[0]+index_xlim
    b = find_peaks(d,height=noise,distance=distance)[0]+index_xlim
    for p_i in p:
        temp_array = data_x[b] - data_x[p_i]
        i = np.where(temp_array > 0, temp_array, np.inf)
        if len(i)==0:
            continue
        b_i = b[i.argmin()]
        if p_i<b_i:
            if len(fc.data['peakindex'])!=0 and data_x[int(p_i)]-data_x[int(fc.data['peakindex'][-1])]<fc.data['arg']['xsens']:
                continue
            y = rotate(data_x[p_i - distance:b_i], data_y[p_i - distance:b_i], distance, -0.07)
            p_i = p_i - distance + np.argmax(y)
            k = np.polyval(np.polyder(np.polyfit(data_x[b_i:b_i + 300][:, 0], data_y[b_i:b_i + 300][:, 0], 1)), data_x[b_i])
            y = rotate(data_x[p_i:b_i + distance], data_y[p_i:b_i + distance], b_i - p_i, k - 0.07)
            b_i = p_i + np.argmin(y)
            fsens = data_y[p_i]-data_y[b_i]
            if fsens > fc.data['arg']['sens']:
                fc.data['peakindex'] = np.append(fc.data['peakindex'],p_i)
                fc.data['bottomindex'] = np.append(fc.data['bottomindex'],b_i)
    fc.data['peakindex'] = list(fc.data['peakindex'].astype(np.uint16))
    fc.data['bottomindex'] = list(fc.data['bottomindex'].astype(np.uint16))
    pass
def wlcfit(fc):
    fc.data['wlcarg'] = []
    fc.data['slopepre'] = []
    n = 50
    data = fc.get_prodata()['retract']
    data_x,data_y = data['measuredHeight'].reshape(-1)*1e9,data['vDeflection'].reshape(-1)*1e12
    lp=fc.data['arg']['lp']
    for i,p_i in enumerate(fc.data['peakindex']):
        b_i = np.where(p_i>fc.data['bottomindex'])[0]
        if len(b_i)!=0:
            b_i = fc.data['bottomindex'][b_i[-1]]
        else:
            temp = p_i
            while temp-n>0:
                k = get_slope(data_x[temp - n:temp], data_y[temp - n:temp])
                if k < 0.01 or data_x[temp] < 10:
                    if temp == p_i:
                        temp -= 10
                    break
                else:
                    temp -= n
            b_i = temp
            if b_i==p_i:
                b_i-=3
        if data_y[p_i]>150:
            dy = data_y[p_i]-data_y[b_i]
            fitpoint = np.where(data_y[b_i:]>data_y[b_i]+0.6*dy)[0][0]+b_i
        else:
            fitpoint = p_i
        if fitpoint==b_i:
            fitpoint+=20
        try:
            popt, _ = curve_fit(lcfunc, data_x[b_i:fitpoint], data_y[b_i:fitpoint],
                                    bounds=([data_x[p_i], lp[0]], [data_x[p_i] + 50, lp[1]]))
        except:
            popt = (WRC_transformer(data_y[b_i:fitpoint],data_x[b_i:fitpoint],thr=5)[1].mean(),0.36)
        try:
            popt_pre, _ = curve_fit(lcfunc, data_x[b_i:p_i], data_y[b_i:p_i],
                                    bounds=([data_x[p_i], 0], [data_x[p_i] + 50, 0.5]))
        except:
            popt_pre = (WRC_transformer(data_y[b_i:p_i],data_x[b_i:p_i],thr=5)[1].mean(),0.36)
        lc, p = popt
        fc.data['wlcarg'].append((lc, p))
        fc.data['slopepre'].append((popt_pre[0],popt_pre[1]))
    fc.data['wlcarg'] = list(fc.data['wlcarg'])
def peakH(fc):
    peakindex = copy.deepcopy(fc.data['peakindex'])
    fc.data['peakindex']=[]
    data = fc.get_prodata()['retract']
    data_y = data['vDeflection'].reshape(-1)*1e12
    for p_i in peakindex:
        if data_y[p_i]>=fc.data['arg']['peakH']:
            fc.data['peakindex'].append(p_i)
def peakN(fc):
    peakN=fc.data['arg']['peakN']
    peaknum = len(fc.data['peakindex'])
    if peaknum >= peakN[0] and peaknum <= peakN[1]:
        fc.data['peaknum_judge'] = True
    else:
        fc.data['peaknum_judge'] = False
def slope(fc):
    fc.data['k'] = np.array([])
    data = fc.get_prodata()['retract']
    data_x,data_y = data['measuredHeight'].reshape(-1)*1e9,data['vDeflection'].reshape(-1)*1e12
    if fc.data['tasktype']=='smfs':
        for i,arg in enumerate(fc.data['slopepre']):
            k = lcfunc1d(data_x[fc.data['peakindex'][i]],*arg)
            fc.data['k'] = np.append(fc.data['k'],k)
        del fc.data['slopepre']
    elif fc.data['tasktype']=='cell_curve':
        n = int(0.05*len(data_x))
        for i,p_i in enumerate(fc.data['peakindex']):
            if len(data_x[p_i-n:p_i])>0:
                x,y = data_x[p_i-n:p_i],data_y[p_i-n:p_i]
                k = get_slope(x, y)
            else:
                k = 5
            fc.data['k'] = np.append(fc.data['k'],k)
    fc.data['k'] = list(fc.data['k'])
def countdlc(fc):
    lc = np.array([])
    for arg in fc.data['wlcarg']:
        lc = np.append(lc,arg[0])
    fc.data['dlc'] = np.diff(lc)
def mkbaseondlc(fc):
    dic=fc.data['arg']['mark']
    fc.data['mark'] = []
    dlc = fc.data['dlc']
    for i in range(len(dlc)):
        for m, rang in dic.items():
            if dlc[i] > rang[0] and dlc[i] < rang[1]:
                fc.data['mark'].append(m)
        if len(fc.data['mark']) - 1 != i:
            fc.data['mark'].append('none')
def findpeak_smallrange(data_y,height=10):
    for prominence in range(3,60,2):
        p,h = find_peaks(data_y,height=height,prominence=15,distance=10)
        if len(p)<3:
            break
    return p
def allrun(fc):
    noise_down(fc)
    cal_baseline_drift(fc)
    cal_baseline_y(fc)
    cal_baseline_x(fc)
    predict(fc)
    findpeak(fc)
    wlcfit(fc)
    peakH(fc)
    peakN(fc)
    slope(fc)
    countdlc(fc)
    mkbaseondlc(fc)
def qmWLC_transformer(f,x,thr=30,p=0.36):
    x = x[np.where(f>thr)]*1e-9
    f = f[np.where(f>thr)]*1e-12
    kb = 1.38e-23
    T = 298
    p = p*1e-9
    gama1 = 27.4e-9
    gama2 = 109.8e-9
    ff = f*p/kb/T
    b = np.exp(np.sqrt(900/ff))
    Lc = x/(4/3-4/3/np.sqrt(ff+1)-10*b/np.sqrt(ff)/((b-1)**2)+ff**1.62/(3.55+3.8*ff**2.2))
    L_0 = Lc/(1/2/gama1*np.sqrt(gama1**2+4*gama2*f+2*gama2-gama1))
    state_L = L_0/2/gama2*(np.sqrt(4*f*gama2+gama1**2)-gama1+2*gama2)
    return f*1e12,state_L*1e13
def WRC_transformer(f,x,thr=20):
    b,gama = 0.11e-9,41/180*np.pi
    kb = 1.38e-23
    T = 298
    x = x[np.where(f>thr)]*1e-9
    f = f[np.where(f>thr)]*1e-12
    l=b*np.cos(gama/2)/np.abs(np.log(np.cos(gama)))
    f_b = kb*T*l/b**2
    x1 = x[np.where(f<f_b)]/(1-(4*f[np.where(f<f_b)]*l/kb/T)**(-0.5))
    x2 = x[np.where(f>=f_b)]/(1-(2*f[np.where(f>=f_b)]*b/kb/T)**(-1))
    return np.hstack((f[np.where(f<f_b)],f[np.where(f>=f_b)]))*1e12,np.hstack((x1,x2))*1e9
def WLC_transformer(f,x,thr=20):
    x = x[np.where(f>thr)].astype(complex)*1e-9
    f = f[np.where(f>thr)].astype(complex)*1e-12
    p = np.array([0.36e-9],dtype=complex)
    lc = wlc2lc(x,f,p)
    return f,lc
def mlti_Gaussian(x, *params):
    y = np.zeros_like(x)
    for i in range(0, len(params), 3):
        ctr = params[i]
        amp = params[i+1]
        wid = params[i+2]
        y = y + amp * np.exp( -((x - ctr)/wid)**2)
    return y
def Lc_transformer(data_x,data_y,plottype='hist'):
    fig,ax = plt.subplots(figsize=(10,6),dpi=300)
    f,x = WRC_transformer(data_y,data_x)
    if plottype=='scatter':
        ax.scatter(x,f,s=2,c='#495057')
        img = fig2img(fig)
        plt.close()
        return img
    a=ax.hist(x,bins=int(x.max()-x.min()))
    kde = KernelDensity(kernel='gaussian', bandwidth=2).fit(x.reshape(-1,1))
    x_ = np.linspace(x.min(),x.max(),int(x.max()-x.min()))
    log_dens = kde.score_samples(x_.reshape(-1,1))
    p,_ = find_peaks(np.exp(log_dens)/np.exp(log_dens).max(),height=0.15,distance=5)
    guess = []
    bound_start = []
    bound_end = []
    for i in p:
        guess += [x_[i], 25, 1]   
        bound_start += [x_[i]-20,0,0]
        bound_end += [x_[i]+20,100,20]
    X = a[1]
    Y = np.append(a[0],0)
    popt, pcov = curve_fit(mlti_Gaussian, X, Y, p0=guess,bounds=(bound_start,bound_end))
    lc = popt[::3]
    for i,l in enumerate(lc):
        if i<len(lc)-1:
            if i%2==0:
                ax.text(l,a[0].max()+10,str(round(lc[i+1]-l,1)),c='b')
            else:
                ax.text(l,a[0].max()+5,str(round(lc[i+1]-l,1)),c='b')
    fit = mlti_Gaussian(x_, *popt)
    ax.plot(x_, fit , 'r')
    ax.set_xlim((lc[0]-30,lc[-1]+50))
    img = fig2img(fig)
    plt.close()
    return img
def plotmap(arr):
    lens = int(np.sqrt(len(arr)))
    arr = arr[:lens**2]
    d = arr.reshape((lens,lens))
    d[1::2]=d[1::2][:,::-1]
    fig,ax = plt.subplots(figsize=(8,6),dpi=300)
    plt.axis('off')
    cmap = plt.get_cmap('YlOrBr_r')
    im = ax.pcolormesh(np.arange(lens),np.arange(lens),d,cmap=cmap,shading='auto')
    bar = fig.colorbar(im)
    bar.set_label('Force(pN)')
    img = fig2img(fig)
    plt.close()
    return img
    pass
def plothist(arr):
    fig,ax = plt.subplots(figsize=(8,6),dpi=300)
    ax.hist(arr,bins=50)
    img = fig2img(fig)
    plt.close()
    return img