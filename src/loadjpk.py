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
from jpkfile import JPKFile, JPKMap
import zipfile
from zipfile import ZipFile
from scipy.signal import savgol_filter
from nanoscope import files
from nanoscope.constants import FORCE, METRIC, VOLTS, PLT_kwargs


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
                     'offset': {'x': 0, 'y': 0, 'k': 0},
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
                data[k]['vDeflection'] = rotate(data[k]['measuredHeight'].reshape(-1),
                                                data[k]['vDeflection'].reshape(-1), -1,
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
            elif sum([True for i in ['.spm'] if fname.endswith(i)]):
                with files.ForceVolumeFile(fname) as f:
                    fv_pixels = f.force_curves_channel.number_of_force_curves
                    for i in range(fv_pixels):
                        self.datalst.append((fname, i))

    def get_filenamelst(self, Travel=True):
        if os.path.isfile(self.filedir):
            self.filelst.append(self.filedir)
        elif os.path.isdir(self.filedir):
            for a, b, c in os.walk(self.filedir, topdown=True, onerror=None, followlinks=False):
                for filename in c:
                    if sum([True for i in ['.txt', '.jpk-force', '.jpk-force-map', '.datay', 'spm'] if
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
        elif filename.endswith('.spm'):
            self.extract_spm_data(filename, index)

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
        jpk = JPKFile(filename)
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
        jpks = JPKMap(filename)
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

    def extract_spm_data(self, fname, index):
        with files.ForceVolumeFile(fname) as f:
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
            self.data['springConstant'] = f.spring_constant

    def extract_all_map2datay(self, todir):
        dic = self.data_structure
        for filename in self.filelst:
            print(filename)
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
            elif filename.endswith('.jpk-force-map'):
                jpk = JPKFile(filename)
                try:
                    springConstant = float(
                        jpk.shared_parameters['lcd-info']['2']['conversion-set']['conversion']['force']['scaling'][
                            'multiplier'])
                except:
                    continue
                dic['springConstant'] = springConstant
                fname = "{}-{}.datay".format(os.path.splitext(os.path.basename(filename))[0], 0)
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

    def changedforce(self, svfname=''):
        if len(self.change) == 0:
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
            if data_y.max()>=0:
                arr = np.append(arr,data_y.max())
            else:
                arr = np.append(arr,0)
        with open('maxforce.txt','w') as f:
            np.savetxt(f,arr)
        return arr
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
            force = fc1.get_prodata()['retract']['vDeflection'][:, 0][fc1.data['peakindex']] * 1e12
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
        wk_i.save('outputdata base on index of {}.xls'.format(os.path.splitext(os.path.basename(self.fname))[0]))
        wk_m.save('outputdata base on mark of {}.xls'.format(os.path.splitext(os.path.basename(self.fname))[0]))