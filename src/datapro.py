
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 09:16:35 2021
@author: ZhengBin
"""
import numpy as np
import copy
from scipy.signal import savgol_filter, find_peaks, medfilt
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt
import torchvision.transforms as transforms
import torch
from PIL import Image
import matplotlib as mpl
from sklearn.neighbors import KernelDensity
mpl.rcParams['font.family'] = 'Arial'
mpl.rcParams['axes.labelsize'] = 8
mpl.rcParams['axes.labelweight'] = 'normal'
mpl.rcParams['axes.linewidth'] = 0.5
mpl.rcParams['font.size'] = 8
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.spines.top'] = False
    

def func(x, k, b):
    return k * x + b

def lcfunc(x, lc, lp):
    return 1.3806e-23 * 298 / (lp * 1e-9) * (1 / 4 * (1 - x / lc) ** (-2) + x / lc - 1 / 4) * 1e12


def rotate(data_x, data_y, index, k):
    theta = np.arctan(k) * -1
    return (data_x - data_x[index]) * np.sin(theta) + (data_y - data_y[index]) * np.cos(theta) + data_y[index]


def loadmodel():
    global model, device, transform
    model = torch.load(r'./model/2021-04-26-01-mobilenet_v2-1.7.1-model.pkl', map_location='cpu')
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.eval()
    transform = transforms.Compose([transforms.Resize(224), transforms.ToTensor(), ])


loadmodel()


def feature_extract(data_y):
    peakindex, _ = find_peaks(data_y, height=25, prominence=40, width=30)
    # 1st_D of vDeflection
    y_1d = -np.gradient(data_y)
    y_1d_bkup = y_1d
    # smooth 1st_D
    y_1d = medfilt(y_1d, 9)
    y_1d_bkup[y_1d < 5] = 0
    y_1d_bkup[y_1d_bkup < 0] = 0
    arr = np.argwhere(y_1d_bkup > 0).reshape(-1)
    # remove near peak of 1st_D
    lst1 = []
    lst2 = []
    for i in range(len(arr)):
        if i + 1 < len(arr) and arr[i] + 3 > arr[i + 1]:
            lst2.append(arr[i])
        elif i == len(arr):
            lst2.append(arr[i])
            lst1.append(lst2)
            lst2 = []
        else:
            lst2.append(arr[i])
            lst1.append(lst2)
            lst2 = []
    for i in lst1:
        lst2.append(int(np.mean(i)))
    for i in range(len(data_y)):
        if i not in peakindex:
            data_y[i] = 0
    for i in range(len(y_1d_bkup)):
        if i not in lst2:
            y_1d_bkup[i] = 0
    fig = plt.figure(figsize=(2.24, 2.24))
    ax = fig.add_subplot(111)
    plt.axis('off')
    plt.subplots_adjust(top=1, bottom=0.1, right=1, left=0.1)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    # preparation of normolazation
    if np.max(y_1d_bkup) == 0:
        a_max = 1
    else:
        a_max = np.max(y_1d_bkup)
    if np.max(data_y) == 0:
        y_max = 1
    else:
        y_max = np.max(data_y)
    ax.plot(y_1d_bkup / a_max, color='#FF0000', linewidth=0.8)
    ax.plot(data_y / y_max * -1, '#0000FF', linewidth=0.8)
    plt.close()
    return fig


def feature(fc):
    data_y = fc.get_prodata(tip_correc=False, s=53)['retract']['vDeflection'][:, 0] * 1e12
    peakindex, _ = find_peaks(data_y, height=30, prominence=14, width=14, distance=50)

    d = fc.get_prodata(tip_correc=False, s=13)['retract']['vDeflection'][:, 0] * 1e12
    d = d / d.max()
    d1 = np.gradient(data_y)
    d1 = d1 / d1.max()
    d1_peakindex, _ = find_peaks(d1, height=0.15, distance=100)
    if len(d1_peakindex) > len(peakindex):
        d1_peakindex = d1_peakindex[d1[d1_peakindex].argsort()[::-1]][:len(peakindex)]
    for i, _ in enumerate(d):
        if i not in peakindex:
            d[i] = 0
    for i, _ in enumerate(d1):
        if i not in d1_peakindex:
            d1[i] = 0
    fig, ax = plt.subplots(figsize=(2.24, 2.24))
    plt.axis('off')
    plt.subplots_adjust(top=1, bottom=0.1, right=1, left=0.1)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    ax.plot(d, color='#FF0000', linewidth=1, alpha=0.9)
    ax.plot(d1 * -1, '#0000FF', linewidth=1, alpha=0.9)
    plt.close()
    return fig


def fig2img(fig):
    fig.canvas.draw()
    img = Image.frombytes('RGB', fig.canvas.get_width_height(), fig.canvas.tostring_rgb())
    return img


def noise_down(fc):
    data_y = fc.data['rawdata']['retract']['vDeflection'] * 1e12
    r = 0.9
    data_y_right = data_y[:, 0][int(r * len(data_y)):]
    data_y_right_smth = savgol_filter(data_y_right, 399, 2)
    for s in np.arange(100)[3::2]:
        err = np.abs(savgol_filter(data_y[:, 0][int(r * len(data_y)):], s, 2) - data_y_right_smth).mean()
        if err < 2:
            break
    print(s)
    fc.data['filters']['win_lens'] = s


def cal_baseline(forcecurve):
    data = copy.deepcopy(forcecurve.data['rawdata']['retract'])
    data['vDeflection'] = savgol_filter(data['vDeflection'][:, 0], 29, 2).reshape(len(data['vDeflection']), 1)
    xy_data = data[int(0.9 * len(data['measuredHeight'])):]
    forcecurve.data['offset']['y'] = xy_data['vDeflection'].mean()
    data['vDeflection'] = data['vDeflection'] - forcecurve.data['offset']['y']
    for i, v in enumerate(data['vDeflection']):
        if v * data['vDeflection'][i + 1] < 0:
            forcecurve.data['offset']['x'] = 0.5 * (data['measuredHeight'][i] + data['measuredHeight'][i + 1])
            break
    # forcecurve.data['offset']['x'] = data['measuredHeight'][:,0][np.where(np.abs(data['vDeflection'][:,0])<1e-12)[0][0]]
    data['measuredHeight'] = data['measuredHeight'] - forcecurve.data['offset']['x']


def cal_baseline_cell(fc):
    fc.data['offset']['x'], fc.data['offset']['y'], fc.data['offset']['k'] = 0, 0, 0
    data = copy.deepcopy(fc.data['rawdata']['retract'])
    fc.data['offset']['y'] = data['vDeflection'][int(0.9 * len(data['vDeflection'])):].mean()
    fc.data['offset']['x'] = data['measuredHeight'].min()
    data['vDeflection'] = savgol_filter(data['vDeflection'][:, 0], fc.data['filters']['win_lens'], 2).reshape(
        len(data['vDeflection']), 1) * -1
    
    left_data = data[int(0.7 * len(data['measuredHeight'])):]
    p = np.polyfit(left_data['measuredHeight'].reshape(-1), left_data['vDeflection'].reshape(-1), 1)
    d = np.polyder(p)
    k = np.polyval(d, left_data['measuredHeight'].reshape(-1)[-1])
    #data['vDeflection'] = rotate(data['measuredHeight'].reshape(-1), data['vDeflection'].reshape(-1), -1, k).reshape(-1,1)
    fc.data['offset']['k'] = k

def predict(forcecurve, get_img=False):
    fig = feature(forcecurve)
    img = fig2img(fig)
    img = transform(img)
    img = img.unsqueeze(0)
    img = img.to(device)
    with torch.no_grad():
        py = model(img)
    pb = torch.nn.functional.softmax(py, dim=1)
    _, predicted = torch.max(pb, 1)
    classIndex_ = predicted[0]
    if classIndex_.item() < 1:
        forcecurve.data['mobilenet_judge'] = True
    else:
        forcecurve.data['mobilenet_judge'] = False
    if get_img:
        return fig


# execute after calbaseline
def findpeak(forcecurve):
    height=forcecurve.data['arg']['peakH']
    sens=forcecurve.data['arg']['sens']
    xlim=forcecurve.data['arg']['xlim']
    forcecurve.data['peakindex'] = []
    data_y = forcecurve.get_prodata(tip_correc=False, s=55)['retract']['vDeflection'][:, 0] * 1e12
    p, _ = find_peaks(data_y, height=height, prominence=sens, width=6, distance=25)
    data = forcecurve.get_prodata(tip_correc=False)['retract']
    data_y = data['vDeflection'][:, 0] * 1e12
    data_x = data['measuredHeight'][:, 0] * 1e9
    p1, _ = find_peaks(data_y, height=height, prominence=sens, width=6, distance=25)
    peak_index = np.array([])
    for n in p:
        idx = (np.abs(p1 - n)).argmin()
        if len(peak_index) != 0:
            temp = (p1[idx] - peak_index)
            if temp.min() < 25:
                if data_y[temp.argmin()] > p1[idx]:
                    continue
                else:
                    peak_index = np.delete(peak_index, temp.argmin())
        peak_index = np.append(peak_index, p1[idx])
    peak_index = peak_index.astype(np.int)
    x_judge = data_x[peak_index] > xlim
    peak_index = peak_index[x_judge]
    forcecurve.data['peakindex'] = peak_index
    return peak_index


# must after cal_baseline_cell
def findpeakbottom_cell(fc):
    data = fc.get_prodata()['retract']
    data_y = data['vDeflection'] * 1e12
    data_x = data['measuredHeight'] * 1e9
    if data_y[:, 0][0] > data_y[:, 0][400:].min():
        return None
    find_range = int(0.1 * len(data_y))
    d = np.gradient(np.gradient(gaussian_filter(data_y[:, 0], 39)))[find_range:]
    d = d / d.max() * -1
    p = find_peaks(d, height=0.6, distance=50)[0] + find_range
    b = find_peaks(d * -1, height=0.5, distance=50)[0] + find_range
    n = 100
    f_boundary = 10
    for p_ in p:
        temp_array = data_x[b] - data_x[p_]
        i = np.where(temp_array > 0, temp_array, np.inf)
        if len(i) > 0:
            i = i.argmin()
        else:
            return None
        b_ = b[i]
        if data_x[b_][0]-data_x[p_][0]<80 and p_ < b_:
            if len(fc.data['peakindex']) > 0 and data_x[p_] - data_x[fc.data['peakindex'][-1]] < 50:
                continue
            y = rotate(data_x[p_ - n:b_], data_y[p_ - n:b_], n, -0.07)
            p_ = p_ - n + np.argmax(y)
            k = np.polyval(np.polyder(np.polyfit(data_x[b_:b_ + 300][:, 0], data_y[b_:b_ + 300][:, 0], 1)), data_x[b_])
            y = rotate(data_x[p_:b_ + n], data_y[p_:b_ + n], b_ - p_, k - 0.07)
            b_ = p_ + np.argmin(y)
            if data_y[p_] - data_y[b_] > f_boundary and data_y[p_] - data_y[b_:b_ + 40].max() > f_boundary:
                fc.data['peakindex'].append(p_)
                fc.data['bottomindex'].append(b_)
    '''
    if len(fc.data['bottomindex'])==0:
        return None
    r = fc.data['bottomindex'][-1]/len(data_y)
    if r<0.7:
        r=0.7
    elif r>0.9:
        r=0.9
    del data
    data = fc.data['rawdata']['retract']
    right_data = data[int(r * len(data['measuredHeight'])):]
    p = np.polyfit(right_data['measuredHeight'].reshape(-1), right_data['vDeflection'].reshape(-1), 1)
    d = np.polyder(p)
    fc.data['offset']['k'] = np.polyval(d, right_data['measuredHeight'].reshape(-1)[-1])
    '''
    # return bottom_index.astype(np.int16),peak_index.astype(np.int16)


# must execute after findpeak
def findbottom(forcecurve):
    forcecurve.data['bottomindex'] = []
    peak_index = forcecurve.data['peakindex']
    data = forcecurve.get_prodata()['retract']
    data_y = data['vDeflection'][:, 0] * 1e12
    data_x = data['measuredHeight'][:, 0] * 1e9
    for i, p_i in enumerate(peak_index):
        if i == 0:
            temp = p_i
            while True:
                k = curve_fit(func, data_x[temp - 50:temp], data_y[temp - 50:temp])[0][0]
                if k < 0.01 or data_x[temp] < 10:
                    if temp == p_i:
                        temp -= 10
                    forcecurve.data['bottomindex'].append(temp)
                    break
                else:
                    temp -= 50
        else:
            temp = peak_index[i - 1] + np.argmin(data_y[peak_index[i - 1]:peak_index[i]])
            forcecurve.data['bottomindex'].append(temp)


# must execute after findbottom
def wlcfit(forcecurve):
    lp=forcecurve.data['arg']['lp']
    forcecurve.data['wlcarg'] = []
    data = forcecurve.get_prodata()['retract']
    data_y = data['vDeflection'][:, 0] * 1e12
    data_x = data['measuredHeight'][:, 0] * 1e9
    peak_index = forcecurve.data['peakindex']
    bottom_index = forcecurve.data['bottomindex']
    boundary_force = 150  # doi: 10.3389/fmolb.2020.00085
    for i in range(len(peak_index)):
        p_i = peak_index[i]
        b_i = bottom_index[i]
        if data_y[p_i] > boundary_force:
            y_distance = data_y[p_i] - data_y[b_i]
            y_fitpoint = data_y[b_i] + 0.3 * y_distance
            if len(np.where(data_y[b_i:] > y_fitpoint)[0]) != 0:
                fitpoint = np.where(data_y[b_i:] > y_fitpoint)[0][0] + b_i
            else:
                x_distance = data_x[p_i] - data_x[b_i]
                x_fitpoint = data_x[b_i] + 0.4 * x_distance
                fitpoint = np.where(data_x[b_i:] > x_fitpoint)[0][0] + b_i
            if len(data_x[b_i:fitpoint]) < 50:
                fitpoint = p_i
            try:
                popt, _ = curve_fit(lcfunc, data_x[b_i:fitpoint], data_y[b_i:fitpoint],
                                    bounds=([data_x[p_i], lp[0]], [data_x[p_i] + 50, lp[1]]))
            except:
                popt = (0, 0)
                # print(err)
        else:
            try:
                popt, _ = curve_fit(lcfunc, data_x[b_i:p_i], data_y[b_i:p_i],
                                    bounds=([data_x[p_i], lp[0]], [data_x[p_i] + 50, lp[1]]))
            except:
                popt = (0, 0)
        lc, p = popt
        forcecurve.data['wlcarg'].append((lc, p))


def cleanpeak(forcecurve):
    peak_index = forcecurve.data['peakindex']
    bottom_index = forcecurve.data['bottomindex']
    wlcarg = forcecurve.data['wlcarg']
    accept_lst = []
    for i in range(len(wlcarg)):
        if sum(wlcarg[i]) != 0:
            accept_lst.append(i)
    if len(accept_lst) != 0:
        forcecurve.data['peakindex'] = []
        forcecurve.data['bottomindex'] = []
        forcecurve.data['wlcarg'] = []
        for i in accept_lst:
            forcecurve.data['peakindex'].append(peak_index[i])
            forcecurve.data['bottomindex'].append(bottom_index[i])
            forcecurve.data['wlcarg'].append(wlcarg[i])


# must execute after wlcfit and cleanpeak
def countdlc(fc):
    fc.data['dlc'] = []
    wlcarg = fc.data['wlcarg']
    for i in range(len(wlcarg)):
        if i != len(wlcarg) - 1:
            fc.data['dlc'].append(wlcarg[i + 1][0] - wlcarg[i][0])


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


def peaknumjudge(fc):
    peakN=fc.data['arg']['peakN']
    peaknum = len(fc.data['peakindex'])
    if peaknum >= peakN[0] and peaknum <= peakN[1]:
        fc.data['peaknum_judge'] = True
    else:
        fc.data['peaknum_judge'] = False


def slope(fc):
    fc.data['k'] = []
    peak_index = fc.data['peakindex']
    bottom_index = fc.data['bottomindex']
    data = fc.get_prodata()['retract']
    data_y = data['vDeflection'][:, 0] * 1e12
    data_x = data['measuredHeight'][:, 0] * 1e9
    for i in range(len(peak_index)):
        x, y = data_x[bottom_index[i]:peak_index[i]], data_y[bottom_index[i]:peak_index[i]]
        if len(x) > 150:
            deg = 5
        else:
            deg = 1
        re = np.polyfit(x, y, deg)

        d = np.polyder(re)
        k = np.polyval(d, data_x[peak_index[i]])
        b = data_y[peak_index[i]] - k * data_x[peak_index[i]]
        fc.data['k'].append((k, b))


def graph(forcecurve):
    fig, ax = plt.subplots(dpi=300, figsize=(8, 5))
    data = forcecurve.get_prodata()['retract']
    data_y = data['vDeflection'][:, 0] * 1e12
    data_x = data['measuredHeight'][:, 0] * 1e9
    peak_index = forcecurve.data['peakindex']
    bottom_index = forcecurve.data['bottomindex']
    ax.plot([-5, 5], [0, 0], 'r-', lw=1)
    ax.plot([0, 0], [-50, 50], 'r-', lw=1)
    ax.set_xlim([-5, data_x[peak_index[-1]] + 40])
    ax.set_yticks(np.arange(0, data_y.max(), 150))
    ax.plot(data_x, data_y, 'k', lw=0.5)
    ax.plot(data_x[peak_index], data_y[peak_index], 'ro', markersize=2)
    ax.plot(data_x[bottom_index], data_y[bottom_index], 'g*', markersize=7)
    for i in range(len(forcecurve.data['wlcarg'])):
        wlcarg = forcecurve.data['wlcarg'][i]
        if sum(wlcarg) == 0:
            continue
        x_ = np.linspace(0, data_x[peak_index[i]] + 10)
        y_ = lcfunc(x_, *wlcarg)
        ax.plot(x_, y_, '-.', lw=0.5)
    for i in range(len(forcecurve.data['k'])):
        x_ = np.linspace(data_x[peak_index[i]] - 10, data_x[peak_index[i]] + 5)
        y_ = forcecurve.data['k'][i][0] * x_ + forcecurve.data['k'][i][1]
        ax.plot(x_, y_, 'b-.')
    ax.set_ylim([-30, data_y.max() + 40])
    return fig, ax
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
    kde = KernelDensity(kernel='gaussian', bandwidth=1).fit(x.reshape(-1,1))
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
            ax.text(l,-15,str(round(lc[i+1]-l,1)),c='b')
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