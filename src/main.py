# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 14:54:58 2021

@author: ZhengBin
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox
import numpy as np
import copy
from src.loadjpk import forcecurve,loadjpkfile,zipfileopera
from src.datapro import cal_baseline,findpeak,findbottom,wlcfit,cleanpeak,countdlc,mkbaseondlc,predict,peaknumjudge,slope
from src.datapro import cal_baseline_cell,findpeakbottom_cell
smfs_func_lst = [cal_baseline,predict,findpeak,findbottom,wlcfit,cleanpeak,countdlc,mkbaseondlc,peaknumjudge,slope]
cell_func_lst = [cal_baseline_cell,findpeakbottom_cell,peaknumjudge]
def process_customize(fc,functions=[0],tasktype='smfs'):
    if tasktype == 'smfs':
        func_lst = smfs_func_lst
    elif tasktype == 'cell_curve':
        func_lst = cell_func_lst
    for i in functions:
        func_lst[i](fc)
def main_smfs(fc,zpo):
    if fc.data['rawdata'] == {}:
        return None
    process_customize(fc, [0, 2, 3, 4, 5, 6, 7, 8])
    if not fc.data['peaknum_judge']:
        return None
    process_customize(fc, [1])
    if not fc.data['mobilenet_judge']:
        return None
    zpo.changingforce(fc)
def main_cell(fc,zpo):
    if fc.data['rawdata'] == {}:
        return None
    process_customize(fc, [0,1,2],'cell_curve')
    if not fc.data['peaknum_judge']:
        return None
    zpo.changingforce(fc)
def main(fc,zpo,tasktype='smfs'):
    if tasktype=='smfs':
        main_smfs(fc,zpo)
    elif tasktype=='cell_curve':
        main_cell(fc,zpo)
class programbody():
    def __init__(self):
        self.tasktype = 'smfs'
        self.forcecurve_index = 0
        self.forcepeak_index = 0
        self.Realpeakindex = 0
        self.ready_run = False
        self.state = False
        self.change_dic = {}
    def creattask(self,path,tasktype='smfs'):
        self.tasktype = tasktype
        self.fc = forcecurve()
        if path.endswith('.DataYee-force'):
            self.zpo = zipfileopera(path)
            self.ljp = loadjpkfile(self.zpo.get_sourcepath())
            self.state = True
        else:
            self.zpo= zipfileopera()
            self.ljp = loadjpkfile(path)
            self.ready_run = True
    def curve_change(self):
        self.change_dic[self.forcecurve_index]=self.fc.data['datamsg']
        self.zpo.changingforce(self.fc)
    def fc_indexchange(self,n=0):
        if self.forcecurve_index+n>len(self.zpo)-1:
            self.forcecurve_index = len(self.zpo)-1
        elif self.forcecurve_index+n<0:
            self.forcecurve_index = 0
        else:
            self.forcecurve_index = self.forcecurve_index+n
    def pk_indexchange(self,n):
        peaklength = len(self.fc.data['peakindex'])
        if peaklength == 0:
            self.fc.data['artificial_judge']=False
            return None
        if self.forcepeak_index+n >peaklength-1:
            self.forcepeak_index = peaklength-1
        elif self.forcepeak_index+n<0:
            self.forcepeak_index=0
        else:
            self.forcepeak_index=self.forcepeak_index+n
    def baseline_change(self,n):
        self.fc.data['offset']['y'] += n
        self.curve_change()
        if self.tasktype == 'smfs':
            process_customize(self.fc,range(4,8),self.tasktype)
    def pk_delete(self):
        del self.fc.data['peakindex'][self.forcepeak_index]
        del self.fc.data['bottomindex'][self.forcepeak_index]
        del self.fc.data['wlcarg'][self.forcepeak_index]
        process_customize(self.fc,[6,7],self.tasktype)
        self.pk_indexchange(-1)
        self.curve_change()
    def fc_delete(self):
        self.forcepeak_index = 0
        self.fc.data['artificial_judge']=False
        self.curve_change()
    def lp_change(self,dlp=0,amply=0.1):
        if len(self.fc.data['wlcarg'])==0:
            return None
        real_peakindex = np.argwhere(self.zpo[self.forcecurve_index]['peakindex']==self.fc.data['peakindex'][self.forcepeak_index])[0][0]
        self.fc.data['wlcarg'][self.forcepeak_index]=(self.fc.data['wlcarg'][self.forcepeak_index][0],
                                                 self.zpo[self.forcecurve_index]['wlcarg'][real_peakindex][1]+amply*dlp)
        process_customize(self.fc,[6,7],self.tasktype)
        self.curve_change()
    def lc_change(self,dlc=0,amply=1):
        if len(self.fc.data['wlcarg'])==0:
            return None
        real_peakindex = np.argwhere(self.zpo[self.forcecurve_index]['peakindex']==self.fc.data['peakindex'][self.forcepeak_index])[0][0]
        self.fc.data['wlcarg'][self.forcepeak_index]=(self.zpo[self.forcecurve_index]['wlcarg'][real_peakindex][0]+amply*dlc,
                                                 self.fc.data['wlcarg'][self.forcepeak_index][1])
        process_customize(self.fc,[6,7],self.tasktype)
        self.curve_change()
    def reset(self):
        self.fc.recover_force(self.ljp)
        process_customize(self.fc,range(2,8),'smfs')
        self.fc.data['artificial_judge'] = True
        self.fc.clean_force()
        self.curve_change()
    def savechange(self,name):
        self.zpo.changedforce(name)
        self.change_dict={}
    def plot(self,F):
        if self.forcecurve_index in self.change_dic.keys():
            self.fc.data = copy.deepcopy(self.zpo.change[self.change_dic[self.forcecurve_index]].data)
        else:
            self.fc.data = self.zpo[self.forcecurve_index]
        fc = copy.deepcopy(self.fc)
        fc.recover_force(self.ljp)
        F.plot(fc,self.forcepeak_index)
    def drawlabel(self,label,lclplabel):
        label.setText('Peak select: {}/{}'.format(self.forcecurve_index,len(self.zpo)-1))
        if self.forcepeak_index<len(self.fc.data['peakindex'])-1:
            lclplabel.setText('Lc={:.1f}nm; lp={:.2f}; dLc={:.1f}nm'.format(*self.fc.data['wlcarg'][self.forcepeak_index],self.fc.data['dlc'][self.forcepeak_index]))
        else:
            lclplabel.setText('Lc={:.1f}nm; lp={:.2f}'.format(*self.fc.data['wlcarg'][self.forcepeak_index]))
    def execu_autostep(self,progress):
        if not self.ready_run:
            return None
        num = len(self.ljp)
        progress.setWindowTitle("Please Wait")  
        progress.setLabelText("Processing...")
        progress.setCancelButtonText("Cancel")
        progress.setMinimumDuration(5)
        progress.setWindowModality(Qt.WindowModal)
        progress.setRange(0,num)
        for i,data in enumerate(self.ljp):
            progress.setValue(i)
            if progress.wasCanceled():
                QMessageBox.warning(self,"Warning!","Failed!")
                self.zpo.delet_dataYee()
                break
            self.fc.data = data
            main(self.fc,self.zpo)
        else:
            self.state = True
            self.zpo.saveforce()
            progress.setValue(num)
            QMessageBox.information(self,"Notic","Success")
            self.ready_run = False
if __name__ == '__main__':
    import time,datetime
    t1 = time.time()
    #batch_fc_pro(r'D:\code\py\DataYeeN\20201125-COH-I30-I32-NGL-9GLINKER\20201125-COH-I30-I32-NGL-9GLINKER')
    t2 = time.time()
    print(str(datetime.timedelta(seconds=t2-t1)))