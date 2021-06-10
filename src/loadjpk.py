"""
Created on Mon Apr  5 09:54:58 2021
@author: ZhengBin
"""
import os
import copy
import time
import numpy as np
import pickle
import xlwt
import pandas as pd
from jpkfile import JPKFile, JPKMap
import zipfile
from zipfile import ZipFile
from scipy.signal import savgol_filter
'''from nanoscope import files
from nanoscope.constants import FORCE, METRIC, VOLTS, PLT_kwargs'''


def rotate(data_x, data_y, index, k):
    theta = np.arctan(k) * -1
    return (data_x - data_x[index]) * np.sin(theta) + (data_y - data_y[index]) * np.cos(theta) + data_y[index]


class forcecurve:
    def __init__(self):
        self.data = {'tasktype': '',
                     'rawdata': {},
                     'path': '',
                     'springConstant': 0.01,
                     'datamsg': ('', 0),
                     'offset': {'x': 0, 'y': 0, 'k': 0,'highspeed':0},
                     'filters': {'methods': 'savgol', 'win_lens': 13, 'poly': 2},
                     'mobilenet_judge': True,
                     'peaknum_judge': True,
                     'artificial_judge': True,
                     'peakindex': [],
                     'bottomindex': [],
                     'wlcarg': [],
                     'dlc': [],
                     'k': [],
                     'mark': [],
                     'arg':{}}

    def get_prodata(self, smooth=True, tip_correc=True, s=None):
        data = copy.deepcopy(self.data['rawdata'])
        for k, v in data.items():
            data[k]['measuredHeight'] = data[k]['measuredHeight'] - self.data['offset']['x']
            data[k]['vDeflection'] = data[k]['vDeflection'] - self.data['offset']['y']
            if smooth and k == 'retract':
                if s == None:
                    data[k]['vDeflection'] = savgol_filter(data[k]['vDeflection'][:, 0],
                                                           self.data['filters']['win_lens'],
                                                           self.data['filters']['poly']).reshape(
                        len(data[k]['vDeflection']), 1)
                else:
                    data[k]['vDeflection'] = savgol_filter(data[k]['vDeflection'][:, 0], s, 2).reshape(
                        len(data[k]['vDeflection']), 1)
            data[k]['vDeflection'] *= -1
            if tip_correc:
                data[k]['measuredHeight'] = data[k]['measuredHeight'] - data[k]['vDeflection'] / self.data[
                    'springConstant']
            if 'k' in self.data['offset'].keys():
                if 'rotate_index' in self.data['offset'].keys():
                    rotate_index = self.fc.data['offset']['rotate_index']
                else:
                    rotate_index = -1
                data[k]['vDeflection'] = rotate(data[k]['measuredHeight'].reshape(-1),
                                                data[k]['vDeflection'].reshape(-1),
                                                rotate_index,
                                                self.data['offset']['k']).reshape(-1, 1)
        return data

    def savedata2txt(self, savedir='data.txt'):
        data = self.get_prodata(tip_correc=False)
        data_re = data['retract']
        f = data_re['vDeflection'].reshape(-1)
        h = data_re['measuredHeight'].reshape(-1)
        data2save = np.dstack((f, h))[0]
        now = int(time.time())
        timeArray = time.localtime(now)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        header = ''
        header += otherStyleTime
        header += '\n'
        header += 'springConstant:' + str(self.data['springConstant']) + 'N/m'
        with open(savedir, 'w') as f:
            np.savetxt(f, data2save, header=header, fmt='%.6e')

    def clean_force(self):
        self.data['rawdata'] = {}

    def recover_force(self, ljf):
        ljf.file_type_deter(*self.data['datamsg'])
        self.data['rawdata'] = ljf.data['rawdata']


class loadjpkfile(forcecurve):
    def __init__(self, filedir):
        super().__init__()
        self.filedir = filedir
        self.filelst = []
        self.datalst = []
        self.get_filenamelst()
        self.get_dataindex()
        self.startnum = -1
        self.data_structure = copy.deepcopy(self.data)

    def __len__(self):
        return len(self.datalst)

    def __iter__(self):
        return self

    def __next__(self):
        self.startnum += 1
        if self.startnum < len(self.datalst):
            pass
        else:
            self.startnum = -1
            raise StopIteration
        self.data = copy.deepcopy(self.data_structure)
        self.file_type_deter(*self.datalst[self.startnum])
        self.data['datamsg'] = self.datalst[self.startnum]
        self.data['path'] = self.filedir
        return self.data

    def __getitem__(self, index):
        self.data = copy.deepcopy(self.data_structure)
        self.file_type_deter(*self.datalst[index])
        self.data['datamsg'] = self.datalst[index]
        self.data['path'] = self.filedir
        return self.data

    def get_dataindex(self):
        for fname in self.filelst:
            if sum([True for i in ['.txt', '.jpk-force', '.datay'] if fname.endswith(i)]):
                self.datalst.append((fname, 0))
            elif sum([True for i in ['.jpk-force-map'] if fname.endswith(i)]):
                properties = ZipFile(fname).open('header.properties')
                while True:
                    line = properties.readline()
                    if b'force-scan-map.indexes.max' in line:
                        maxindex = int(line.rstrip().split(b'=')[-1])
                        for i in range(maxindex):
                            self.datalst.append((fname, i))
                        break
            '''elif sum([True for i in ['.spm'] if fname.endswith(i)]):
                with files.ForceVolumeFile(fname) as f:
                    fv_pixels = f.force_curves_channel.number_of_force_curves
                    for i in range(fv_pixels):
                        self.datalst.append((fname, i))'''

    def get_filenamelst(self, Travel=True):
        if os.path.isfile(self.filedir):
            self.filelst.append(self.filedir)
        elif os.path.isdir(self.filedir):
            for a, b, c in os.walk(self.filedir, topdown=True, onerror=None, followlinks=False):
                for filename in c:
                    if sum([True for i in ['.txt', '.jpk-force', '.jpk-force-map', '.datay'] if
                            os.path.join(a, filename).endswith(i)]):
                        self.filelst.append(os.path.join(a, filename))
                if not Travel:
                    break

    def file_type_deter(self, filename, index):
        if filename.endswith('.txt'):
            self.extract_txt_data(filename, index)
        elif filename.endswith('.jpk-force'):
            self.extract_force_data(filename, index)
        elif filename.endswith('.jpk-force-map'):
            self.extract_map_data(filename, index)
        elif filename.endswith('.datay'):
            self.extract_datay_data(filename, index)
        '''elif filename.endswith('.spm'):
            self.extract_spm_data(filename, index)'''

    def extract_txt_data(self, filename, index):
        data = np.loadtxt(filename, comments='#')
        with open(filename, 'r') as f:
            text = f.readlines()
            for line in text:
                if '# springConstant' in line:
                    springConstant = float(line.split()[-1])
                    break
        self.data['springConstant'] = springConstant
        self.data['rawdata']['extend'] = np.array([[tuple(i)] for i in data[:np.argmin(data[:, 0])]],
                                                  dtype=[('measuredHeight', '<f8'), ('vDeflection', '<f8')])
        self.data['rawdata']['retract'] = np.array([[tuple(i)] for i in data[np.argmin(data[:, 0]):]],
                                                   dtype=[('measuredHeight', '<f8'), ('vDeflection', '<f8')])

    def extract_force_data(self, filename, index):
        try:
            jpk = JPKFile(filename)
        except:
            return None
        try:
            springConstant = float(
                jpk.shared_parameters['lcd-info']['2']['conversion-set']['conversion']['force']['scaling'][
                    'multiplier'])
        except:
            return None
        self.data['springConstant'] = springConstant
        for i, segment in jpk.segments.items():
            self.data['rawdata'][segment.get_info('type')] = segment.get_array(['measuredHeight', 'vDeflection'])[0]

    def extract_map_data(self, filename, index):
        try:
            jpks = JPKMap(filename)
        except:
            return None
        jpk = jpks.get_single_pixel(index)
        try:
            springConstant = float(
                jpk.shared_parameters['lcd-info']['2']['conversion-set']['conversion']['force']['scaling'][
                    'multiplier'])
        except:
            springConstant = float(
                jpk.shared_parameters['lcd-info']['1']['conversion-set']['conversion']['force']['scaling'][
                    'multiplier'])
        self.data['springConstant'] = springConstant
        for i, segment in jpk.segments.items():
            self.data['rawdata'][segment.get_info('type')] = segment.get_array(['measuredHeight', 'vDeflection'])[0]

    '''def extract_spm_data(self, fname, index):
        with files.ForceVolumeFile(fname) as f:
            print(fname)
            fc_channel = f.force_curves_channel
            h_sens_chan = f[2]
            fz_plot, ax_prop = fc_channel.create_force_z_plot(index, FORCE)
            h_sens_data = h_sens_chan.get_force_curve_data(index, METRIC)
            if 'nN' in ax_prop['ylabel']:
                factor = 1e-9
            elif 'pN' in ax_prop['ylabel']:
                factor = 1e-12
            data_x = h_sens_data.retrace * -1e-9
            data_y = fz_plot.retrace.y * factor
            data = np.dstack((data_x, data_y))[0]
            self.data['rawdata']['retract'] = np.array([[tuple(i)] for i in data],
                                                       dtype=[('measuredHeight', '<f8'), ('vDeflection', '<f8')])
            self.data['springConstant'] = f.spring_constant'''

    def extract_all_map2datay(self, todir):
        dic = self.data_structure
        for filename in self.filelst:
            if filename.endswith('.jpk-force-map'):
                jpks = JPKMap(filename)
                for i in range(len(jpks.flat_indices)):

                    jpk = jpks.get_single_pixel(i)
                    try:
                        springConstant = float(
                            jpk.shared_parameters['lcd-info']['2']['conversion-set']['conversion']['force']['scaling'][
                                'multiplier'])
                    except:
                        springConstant = float(
                            jpk.shared_parameters['lcd-info']['1']['conversion-set']['conversion']['force']['scaling'][
                                'multiplier'])
                    dic['springConstant'] = springConstant
                    dic['datamsg'] = (filename, i)
                    for n, segment in jpk.segments.items():
                        dic['rawdata'][segment.get_info('type')] = segment.get_array(['measuredHeight', 'vDeflection'])[
                            0]
                    fname = "{}-{}.datay".format(os.path.join(todir, os.path.splitext(os.path.basename(filename))[0]),
                                                 i)
                    with open(fname, 'wb') as f:
                        pickle.dump(dic, f)
            elif filename.endswith('.jpk-force'):
                jpk = JPKFile(filename)
                try:
                    springConstant = float(
                        jpk.shared_parameters['lcd-info']['2']['conversion-set']['conversion']['force']['scaling'][
                            'multiplier'])
                except:
                    continue
                dic['springConstant'] = springConstant
                fname = "{}-{}.datay".format(os.path.join(todir, os.path.splitext(os.path.basename(filename))[0]),0)
                for i, segment in jpk.segments.items():
                    dic['rawdata'][segment.get_info('type')] = segment.get_array(['measuredHeight', 'vDeflection'])[0]
                with open(fname, 'wb') as f:
                    pickle.dump(dic, f)

    def extract_datay_data(self, filename, index):
        with open(filename, 'rb') as f:
            pkl = pickle.load(f)
        springConstant = pkl['springConstant']
        self.data['springConstant'] = springConstant
        self.data['rawdata'] = pkl['rawdata']


class zipfileopera:
    def __init__(self, fname='test.DataYee-force'):
        self.fname = fname
        self.startnum = -1
        self.change = {}

    def __len__(self):
        with ZipFile(self.fname, 'r', zipfile.ZIP_DEFLATED) as zips:
            lens = len(zips.namelist())
        return lens

    def __getitem__(self, index):
        with ZipFile(self.fname, 'r', zipfile.ZIP_DEFLATED) as zips:
            filename = zips.namelist()[index]
            with zips.open(filename) as f:
                data = pickle.load(f)
        return data

    def get_sourcepath(self):
        with ZipFile(self.fname, 'r', zipfile.ZIP_DEFLATED) as zips:
            # zips.extract(zips.namelist()[0])
            with zips.open(zips.namelist()[0]) as f:
                data = pickle.load(f)
        return data['path']

    def addforce(self, fc):
        fc.clean_force()
        o = os.path.splitext(os.path.basename(fc.data['datamsg'][0]))[0] + '-s-' + str(fc.data['datamsg'][1]) + '.pkl'
        pkl = pickle.dumps(fc.data)
        with ZipFile(self.fname, 'a', zipfile.ZIP_DEFLATED) as zips:
            zips.writestr(o, pkl)

    def saveforce(self):
        with ZipFile(self.fname, 'a', zipfile.ZIP_DEFLATED) as zips:
            for i, fcs in self.change.items():
                o = os.path.splitext(os.path.basename(fcs.data['datamsg'][0]))[0] + '-s-' + str(
                    fcs.data['datamsg'][1]) + '.pkl'
                pkl = pickle.dumps(fcs.data)
                zips.writestr(o, pkl)
        self.change = {}

    def changingforce(self, fc):
        bup = copy.deepcopy(fc)
        #        bup.clean_force()
        self.change[fc.data['datamsg']] = bup

    def changedforce(self, svfname='',saveas=False):
        if len(self.change) == 0 and not saveas:
            return None
        with ZipFile(self.fname, 'r', zipfile.ZIP_DEFLATED) as zips:
            lst = copy.deepcopy(zips.namelist())
        pkl_dic = {}
        pkl_index = {}
        with ZipFile(self.fname, 'r', zipfile.ZIP_DEFLATED) as zips:
            for i, arcname in enumerate(lst):
                with zips.open(arcname, 'r') as f:
                    pkl_dic[arcname] = pickle.load(f)
                    pkl_index[i] = arcname
        os.remove(self.fname)
        for i, fcs in self.change.items():
            o = os.path.splitext(os.path.basename(fcs.data['datamsg'][0]))[0] + '-s-' + str(
                fcs.data['datamsg'][1]) + '.pkl'
            pkl_dic[o] = fcs.data
        if svfname != '':
            self.fname = svfname
        with ZipFile(self.fname, 'w', zipfile.ZIP_DEFLATED) as zips:
            for i in range(len(pkl_index)):
                zips.writestr(pkl_index[i], pickle.dumps(pkl_dic[pkl_index[i]]))
        self.change = {}

    def delet_dataYee(self):
        if os.path.isfile(self.fname):
            os.remove(self.fname)
    def get_maxforce(self,ljp,filters=True, filter_lst=['peaknum_judge', 'mobilenet_judge', 'artificial_judge']):
        arr = np.array([])
        for i in range(len(self)):
            fc1 = forcecurve()
            fc1.data = self[i]
            fc1.recover_force(ljp)
            data = fc1.get_prodata()['retract']
            data_y = data['vDeflection']*1e12
            if len(fc1.data['peakindex'])==0:
                arr = np.append(arr,data_y[int(0.8*len(data_y)):].max())
            else:
                arr = np.append(arr,data_y[fc1.data['peakindex']].max())
            continue
            if data_y.max()>=0:
                arr = np.append(arr,data_y.max())
            else:
                arr = np.append(arr,0)
        with open('maxforce.txt','w') as f:
            np.savetxt(f,arr)
        return arr
    def split_bypeakN(self):
        fc = forcecurve()
        dic = {}
        pure_fname = os.path.splitext(self.fname)[0]
        for i,data in enumerate(self):
            fc.data = data
            peakN = fc.data['peakindex']
            if len(peakN) not in dic.keys():
                dic[peakN] = []
            dic[peakN].append(fc)
        for k,v in dic.items():
            fname = '{}-peakN-{}.DataYee-Force'.format(pure_fname,k)
            with ZipFile(fname, 'a', zipfile.ZIP_DEFLATED) as zips:
                for fc in v:
                    o = os.path.splitext(os.path.basename(fc.data['datamsg'][0]))[0] + '-s-' + str(
                        fc.data['datamsg'][1]) + '.pkl'
                    pkl = pickle.dumps(fc.data)
                    zips.writestr(o, pkl)
    def exporttxt(self,ljp,forcecurve_index,tip_correc=True):
        fc = forcecurve()
        fc.data=self[forcecurve_index]
        if not fc.data['artificial_judge']:
            return None
        fc.recover_force(ljp)
        data = fc.get_prodata(tip_correc=tip_correc)
        data_x = data['retract']['measuredHeight']
        data_y = data['retract']['vDeflection']*-1
        x = np.dstack((data_x[:,0],data_y[:,0]))[0]
        if 'extend' in data.keys():
            data_x_e = data['extend']['measuredHeight']
            data_y_e = data['extend']['vDeflection']*-1
            e = np.dstack((data_x_e[:,0],data_y_e[:,0]))[0]
            x = pd.DataFrame(np.vstack((e,np.array([np.nan,np.nan]),x)))
        else:
            x = pd.DataFrame(np.vstack((np.array([[0,0],[np.nan,np.nan]]),x)))
        todir = os.path.join(os.path.dirname(self.fname),'txt_out')
        if not os.path.isdir(todir):
            os.makedirs(todir)
        name = "{}.txt".format(forcecurve_index)
        fname = os.path.join(todir, name)
        header = ['#','SpringConstant: {:.4f}'.format(fc.data['springConstant'])]
        x.to_csv(fname,sep=' ',float_format='%.5e',index=False,header=header)
    def get_arg(self,ljp,f_index=None):
        arg_dic = {'dlc':[],'lc':[],'p':[],'force':[],'k':[],'lens':[]}
        mark_data = {}
        fc = forcecurve()
        max_mark = 0
        pd.set_option('precision', 4)
        for i,data in enumerate(self):
            dlc,lc,p,f,k=[],[],[],[],[]
            if data['artificial_judge']:
                fc.data = data
                fc.recover_force(ljp)
                data_y = fc.get_prodata()['retract']['vDeflection']*1e12
                for index,p_i in enumerate(fc.data['peakindex']):
                    if index<len(fc.data['dlc']):
                        dlc.append(fc.data['dlc'][index])
                        if fc.data['mark'][index] not in mark_data.keys():
                            mark_data[fc.data['mark'][index]]={}
                            mark_data[fc.data['mark'][index]]['dlc']=[]
                            mark_data[fc.data['mark'][index]]['lc'] =[]
                            mark_data[fc.data['mark'][index]]['p'] =[]
                            mark_data[fc.data['mark'][index]]['k'] =[]
                            mark_data[fc.data['mark'][index]]['force'] =[]
                        mark_data[fc.data['mark'][index]]['dlc'].append(fc.data['dlc'][index])
                        mark_data[fc.data['mark'][index]]['lc'].append(fc.data['wlcarg'][index][0])
                        mark_data[fc.data['mark'][index]]['p'].append(fc.data['wlcarg'][index][1])
                        mark_data[fc.data['mark'][index]]['k'].append(fc.data['k'][index])
                        mark_data[fc.data['mark'][index]]['force'].append(data_y[:,0][p_i]+fc.data['offset']['highspeed']*1e12)
                        max_mark = max(max_mark,len(mark_data[fc.data['mark'][index]]['dlc']))
                    lc.append(fc.data['wlcarg'][index][0])
                    p.append(fc.data['wlcarg'][index][1])
                    k.append(fc.data['k'][index])
                    f.append(data_y[:,0][p_i]+fc.data['offset']['highspeed']*1e12)
            arg_dic['dlc'].append(dlc)
            arg_dic['k'].append(k)
            #print(f,arg_dic['force'])
            arg_dic['force'].append(f)
            arg_dic['lc'].append(lc)
            arg_dic['p'].append(p)
            arg_dic['lens'].append(len(f))
            if f_index!=None and i==f_index:
                break
        max_len = max(arg_dic['lens'])
        for i,lens in enumerate(arg_dic['lens']):
            n = max_len - lens
            arg_dic['dlc'][i]+=['']*(n-1)
            arg_dic['k'][i]+=['']*n
            arg_dic['force'][i]+=['']*n
            arg_dic['lc'][i]+=['']*n
            arg_dic['p'][i]+=['']*n
        del arg_dic['lens']
        #return arg_dic
        fname = os.path.join(os.path.dirname(self.fname),"INDEX-{}.xlsx".format(os.path.splitext(os.path.basename(self.fname))[0]))
        if os.path.isfile(fname):
            os.remove(fname)
        writer = pd.ExcelWriter(fname)
        for k,v in arg_dic.items():
            data_frame = pd.DataFrame(v).round(2)
            data_frame.to_excel(writer,sheet_name=k)
        writer.close()
        fname = os.path.join(os.path.dirname(self.fname),"MARK-{}.xlsx".format(os.path.splitext(os.path.basename(self.fname))[0]))
        if os.path.isfile(fname):
            os.remove(fname)
        writer = pd.ExcelWriter(fname)
        for mark,item in mark_data.items():
            for k,v in item.items():
                item[k]+=['']*(max_mark-len(v))
            data_frame = pd.DataFrame(item).round(2)
            data_frame.to_excel(writer,sheet_name=mark)
        writer.close()
        return True
            
            
            
                
            
    def extrac_argdata(self, ljp, filters=True, filter_lst=['peaknum_judge', 'mobilenet_judge', 'artificial_judge']):
        wk_i = xlwt.Workbook(encoding='utf-8')
        ws_i_lc = wk_i.add_sheet('lc')
        ws_i_dlc = wk_i.add_sheet('dlc')
        ws_i_lp = wk_i.add_sheet('lp')
        ws_i_force = wk_i.add_sheet('force')
        wk_m = xlwt.Workbook(encoding='utf-8')
        ws_m_lc = wk_m.add_sheet('lc')
        ws_m_dlc = wk_m.add_sheet('dlc')
        ws_m_lp = wk_m.add_sheet('lp')
        ws_m_force = wk_m.add_sheet('force')
        col_count = 0
        mk_lst = []
        mk_conut = {}
        for i in range(len(self)):
            fc1 = forcecurve()
            fc1.data = self[i]
            fc1.recover_force(ljp)
            if filters and sum([fc1.data[t] for t in filter_lst]) < len(filter_lst):
                continue
            force = fc1.get_prodata()['retract']['vDeflection'][:, 0][fc1.data['peakindex']] * 1e12+fc1.data['offset']['highspeed']*1e12
            lc, lp = np.array(fc1.data['wlcarg'])[:, 0], np.array(fc1.data['wlcarg'])[:, 1]
            dlc = fc1.data['dlc']
            mark = fc1.data['mark']
            for z in range(len(force)):
                ws_i_lc.write(col_count, z, lc[z])
                if z < len(force) - 1:
                    ws_i_dlc.write(col_count, z, dlc[z])
                ws_i_lp.write(col_count, z, lp[z])
                ws_i_force.write(col_count, z, force[z])
            for z in range(len(mark)):
                if mark[z] not in mk_lst:
                    mk_lst.append(mark[z])
                    mk_conut[mark[z]] = 1
                    for ws in [ws_m_lc, ws_m_dlc, ws_m_lp, ws_m_force]:
                        ws.write(0, mk_lst.index(mark[z]), mark[z])
                else:
                    mk_conut[mark[z]] += 1
                ws_m_lc.write(mk_conut[mark[z]], mk_lst.index(mark[z]), lc[z])
                ws_m_dlc.write(mk_conut[mark[z]], mk_lst.index(mark[z]), dlc[z])
                ws_m_lp.write(mk_conut[mark[z]], mk_lst.index(mark[z]), lp[z])
                ws_m_force.write(mk_conut[mark[z]], mk_lst.index(mark[z]), force[z])
            col_count += 1
        todir = os.path.dirname(self.fname)
        wk_i_svname = os.path.join(todir, 'outputdata base on index of {}.xls'.format(os.path.splitext(os.path.basename(self.fname))[0]))
        wk_m_svname = os.path.join(todir, 'outputdata base on mark of {}.xls'.format(os.path.splitext(os.path.basename(self.fname))[0]))
        try:
            wk_i.save(wk_i_svname)
            wk_m.save(wk_m_svname)
        except:
            return False
        return True
    def export_celldata(self,ljp,f_index):
        fc = forcecurve()
        dic = {'abs force':[],'force':[],'k':[],'lens':[]}
        for i,data in enumerate(self):
            fc.data = data
            fc.recover_force(ljp)
            data = fc.get_prodata()['retract']
            data_x,data_y = data['measuredHeight']*1e9,data['vDeflection']*1e12
            af,f,k=[],[],[]
            if not fc.data['artificial_judge']:
                dic['abs force'].append(af)
                dic['force'].append(f)
                dic['k'].append(k)
                dic['lens'].append(0)
                continue
            for i,p_i in  enumerate(fc.data['peakindex']):
                af.append(data_y[p_i][0]+fc.data['offset']['highspeed']*1e12)
                b_i = fc.data['bottomindex'][np.argmin(np.abs(p_i-fc.data['bottomindex']))]
                f.append((data_y[p_i]-data_y[b_i])[0]+fc.data['offset']['highspeed']*1e12)
                k.append(fc.data['k'][i])
            dic['abs force'].append(af)
            dic['force'].append(f)
            dic['k'].append(k)
            dic['lens'].append(len(fc.data['peakindex']))
            if i==f_index:
                break
        max_lens = max(dic['lens'])
        for i,lens in enumerate(dic['lens']):
            dic['abs force'][i] +=['']*(max_lens-lens)
            dic['force'][i] +=['']*(max_lens-lens)
            dic['k'][i] +=['']*(max_lens-lens)
        todir = os.path.dirname(self.fname)
        fname = os.path.join(todir,"cell_curve-{}.xlsx".format(os.path.splitext(os.path.basename(self.fname))[0]))
        try:
            writer = pd.ExcelWriter(fname)
        except:
            return False
        for sheet_name,data in dic.items():
            data_frame = pd.DataFrame(data).round(2)
            data_frame.to_excel(writer,sheet_name=sheet_name)
        writer.close()
        return True