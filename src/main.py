import time
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox
import numpy as np
import copy
import os
import pickle
from src.loadjpk import forcecurve,loadjpkfile,zipfileopera
from src.datapro import cal_baseline,findpeak,findbottom,wlcfit,cleanpeak,countdlc,mkbaseondlc,predict,peaknumjudge,slope
from src.datapro import cal_baseline_cell,findpeakbottom_cell,noise_down
from src.datapro import Lc_transformer,plotmap,plothist
smfs_func_lst = [noise_down,cal_baseline,predict,findpeak,findbottom,wlcfit,cleanpeak,countdlc,mkbaseondlc,peaknumjudge,slope]
cell_func_lst = [noise_down,cal_baseline_cell,findpeakbottom_cell,peaknumjudge]
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
    fc.data['tasktype']='smfs'
    process_customize(fc, [ 1, 3, 4, 5, 6, 7, 8, 9,10])
    if not fc.data['peaknum_judge']:
        return None
    if fc.data['arg']['usemodel']:
        process_customize(fc, [2])
    if not fc.data['mobilenet_judge']:
        return None
    fc.clean_force()
    zpo.changingforce(fc)
def main_cell(fc,zpo):
    if fc.data['rawdata'] == {} or fc.data['rawdata']['retract']['vDeflection'].sum()==0:
        return None
    fc.data['tasktype']='cell_curve'
    process_customize(fc, [0,1,2,3],'cell_curve')
    if not fc.data['peaknum_judge']:
        return None
    fc.clean_force()
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
        self.taskarg = {'peakH': 40,
           'sens': 10,
           'peakN': [1, 6],
           'xlim': 20,
           'lp': (0.34, 0.38),
           'mark': {'GB1': (13, 23), 'I27': (23, 36)},
           'fitjudge': False,
           'usemodel':True,
           'xsens':3}
    def creattask(self,path,tasktype='smfs'):
        self.tasktype = tasktype
        self.fc = forcecurve()
        if path.endswith('.DataYee-force'):
            self.zpo = zipfileopera(path)
            if len(self.zpo)==0:
                return None
            self.ljp = loadjpkfile(self.zpo.get_sourcepath())
            if 'tasktype' in self.zpo[0].keys():
                self.tasktype = self.zpo[0]['tasktype']
            self.forcecurve_index=0
            self.forcepeak_index=0
            self.state = True
        else:
            self.zpo= zipfileopera()
            self.ljp = loadjpkfile(path)
            self.forcecurve_index=0
            self.forcepeak_index=0
            self.ready_run = True
    def curve_change(self):
        if not self.state:
            return None
        self.change_dic[self.forcecurve_index]=self.fc.data['datamsg']
        self.zpo.changingforce(self.fc)
    def fc_indexchange(self,n=0):
        if not self.state:
            return None
        if self.forcecurve_index+n>len(self.zpo)-1:
            self.forcecurve_index = len(self.zpo)-1
        elif self.forcecurve_index+n<0:
            self.forcecurve_index = 0
        else:
            self.forcecurve_index = self.forcecurve_index+n
        self.forcepeak_index = 0
    def pk_indexchange(self,n):
        peaklength = len(self.fc.data['peakindex'])
        if peaklength == 0:
            return None
        if self.forcepeak_index+n >peaklength-1:
            self.forcepeak_index = peaklength-1
        elif self.forcepeak_index+n<0:
            self.forcepeak_index=0
        else:
            self.forcepeak_index=self.forcepeak_index+n
    def baseline_change(self,n):
        if not self.state:
            return None
        self.fc.data['offset']['y'] += n
        self.curve_change()
        if self.tasktype == 'smfs':
            if 'retract' not in self.fc.data['rawdata'].keys():
                self.fc.recover_force(self.ljp)
            self.fc.data['arg'] = self.taskarg
            process_customize(self.fc,range(4,8),self.tasktype)
    def pk_delete(self):
        if not self.state:
            return None
        if len(self.fc.data['peakindex'])>0:
            del self.fc.data['peakindex'][self.forcepeak_index]
            del self.fc.data['bottomindex'][self.forcepeak_index]
            del self.fc.data['k'][self.forcepeak_index]
        if self.tasktype == 'smfs' and len(self.fc.data['wlcarg'])>0 :
            del self.fc.data['wlcarg'][self.forcepeak_index]
            process_customize(self.fc,range(7,9),self.tasktype)
            self.fc.data['arg'] = self.taskarg
            process_customize(self.fc,[6,7],self.tasktype)
        self.pk_indexchange(-1)
        self.curve_change()
    def fc_delete(self):
        if not self.state:
            return None
        self.forcepeak_index = 0
        self.fc.data['artificial_judge']=False
        self.curve_change()
    def lp_change(self,dlp=0,amply=0.1):
        if len(self.fc.data['wlcarg'])==0:
            return None
        self.fc.data['arg'] = self.taskarg
        real_peakindex = np.argwhere(self.zpo[self.forcecurve_index]['peakindex']==self.fc.data['peakindex'][self.forcepeak_index])[0][0]
        self.fc.data['wlcarg'][self.forcepeak_index]=(self.fc.data['wlcarg'][self.forcepeak_index][0],
                                                 self.zpo[self.forcecurve_index]['wlcarg'][real_peakindex][1]+amply*dlp)
        process_customize(self.fc,range(6,9),self.tasktype)
        self.curve_change()
    def lc_change(self,dlc=0,amply=1):
        if len(self.fc.data['wlcarg'])==0:
            return None
        self.fc.data['arg'] = self.taskarg
        real_peakindex = np.argwhere(self.zpo[self.forcecurve_index]['peakindex']==self.fc.data['peakindex'][self.forcepeak_index])[0][0]
        self.fc.data['wlcarg'][self.forcepeak_index]=(self.zpo[self.forcecurve_index]['wlcarg'][real_peakindex][0]+amply*dlc,
                                                 self.fc.data['wlcarg'][self.forcepeak_index][1])
        process_customize(self.fc,range(6,9),self.tasktype)
        self.curve_change()
    def k_change(self,k=1,amply=1):
        if len(self.fc.data['k'])==0:
            return None
        self.fc.data['arg'] = self.taskarg
        real_peakindex = np.argwhere(self.zpo[self.forcecurve_index]['peakindex']==self.fc.data['peakindex'][self.forcepeak_index])[0][0]
        self.fc.data['k'][self.forcepeak_index] = self.zpo[self.forcecurve_index]['k'][real_peakindex]+k*amply
        self.curve_change()
    def pv_change(self,value):
        if not self.state or len(self.fc.data['peakindex'])==0:
            None
        self.fc.recover_force(self.ljp)
        self.fc.data['peakindex'][self.forcepeak_index]+=value
        process_customize(self.fc,[4,5,7,8,10],self.tasktype)
        self.fc.clean_force()
        self.curve_change()
        self.zpo.changedforce()
        self.change_dic={}
    def reset(self):
        if not self.state:
            return None
        self.fc.recover_force(self.ljp)
        self.fc.data['arg'] = self.taskarg
        if self.tasktype == 'smfs':
            process_customize(self.fc,list(range(2,9))+list(range(10,11)),'smfs')
        elif self.tasktype == 'cell_curve':
            process_customize(self.fc,range(1,3),'cell_curve')
        self.fc.data['artificial_judge'] = True
        self.fc.clean_force()
        self.curve_change()
        self.zpo.changedforce()
        self.change_dic={}
    def savechange(self,name):
        if not self.state:
            return None
        self.change_dic={}
        self.zpo.changedforce(name)
    def changemark(self,mark):
        if not self.state or self.tasktype!='smfs':
            return None
        if self.forcepeak_index<len(self.fc.data['mark']):
            self.fc.data['mark'][self.forcepeak_index]=mark
            self.curve_change()
    def plot(self,F):
        if not self.state:
            return None
        if self.forcecurve_index in self.change_dic.keys():
            self.fc.data = copy.deepcopy(self.zpo.change[self.change_dic[self.forcecurve_index]].data)
        else:
            self.fc.data = self.zpo[self.forcecurve_index]
        if 'arg' in self.fc.data.keys():
            self.taskarg = self.fc.data['arg']
        else:
            self.fc.data['arg'] = self.taskarg
        fc = copy.deepcopy(self.fc)
        F.plot(fc,self.forcepeak_index,self.ljp,self.tasktype)
    def plot_contourhist(self):
        if not self.state or self.tasktype != 'smfs':
            return None
        self.fc.recover_force(self.ljp)
        data = self.fc.get_prodata()['retract']
        data_y = data['vDeflection']*1e12
        data_x = data['measuredHeight']*1e9
        img = Lc_transformer(data_x,data_y)
        img.show()
    def plot_contourscatter(self):
        if not self.state or self.tasktype != 'smfs':
            return None
        self.fc.recover_force(self.ljp)
        data = self.fc.get_prodata()['retract']
        data_y = data['vDeflection']*1e12
        data_x = data['measuredHeight']*1e9
        img = Lc_transformer(data_x,data_y,'scatter')
        img.show()
    def adhesionmap(self):
        if not self.state:
            return None
        arr = self.zpo.get_maxforce(self.ljp)
        img = plotmap(arr)
        img.show()
    def adhesionhist(self):
        if not self.state:
            return None
        arr = self.zpo.get_maxforce(self.ljp)
        img = plothist(arr)
        img.show()
    def drawlabel(self,label,lclplabel):
        if not self.state:
            return None
        label.setText('Peak select: {}/{}'.format(self.forcecurve_index,len(self.zpo)-1))
        if self.tasktype!='smfs' or not self.state:
            return None
        if self.forcepeak_index<len(self.fc.data['peakindex'])-1:
            lclplabel.setText(' Lc={:.1f}nm; lp={:.2f}; dLc={:.1f}nm; k={:.1f}'.format(*self.fc.data['wlcarg'][self.forcepeak_index],self.fc.data['dlc'][self.forcepeak_index],self.fc.data['k'][self.forcepeak_index]))
        elif len(self.fc.data['wlcarg'])>0:
            lclplabel.setText(' Lc={:.1f}nm; lp={:.2f}; k={:.1f}'.format(*self.fc.data['wlcarg'][self.forcepeak_index],self.fc.data['k'][self.forcepeak_index]))
    def export_prodata(self):
        if not self.state:
            return None
        if self.tasktype == 'cell_curve':
            pass
        elif self.tasktype == 'smfs':
            self.zpo.extrac_argdata(self.ljp)
    def exporttxt(self):
        if not self.state:
            return None
        if self.tasktype == 'cell_curve':
            pass
        elif self.tasktype == 'smfs':
            self.zpo.exporttxt(self.ljp,self.forcecurve_index)
    def export_figure(self,figure):
        if not self.state:
            return None
        todir = os.path.dirname(self.zpo.fname)
        fname = os.path.join(todir,'{}.png'.format(self.forcecurve_index))
        figure.savefig(fname,bbox_inches='tight',transparent=True)
    def execu_autostep(self,progress,sel):
        if not self.ready_run:
            return None
        self.zpo.delet_dataYee()
        self.change_dic = {}
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
                QMessageBox.warning(sel,"Warning!","Failed!")
                self.zpo.delet_dataYee()
                self.ready_run = False
                break
            self.fc.data = data
            self.fc.data['arg'] = self.taskarg
            main(self.fc,self.zpo,self.tasktype)
        else:
            if len(self.zpo.change)==0:
                self.state = False
            else:
                self.state = True
            self.zpo.saveforce()
            progress.setValue(num)
            QMessageBox.information(sel,"Notic","Success")
            self.ready_run = False
            
if __name__ == '__main__':
    import time,datetime
    t1 = time.time()
    #batch_fc_pro(r'D:\code\py\DataYeeN\20201125-COH-I30-I32-NGL-9GLINKER\20201125-COH-I30-I32-NGL-9GLINKER')
    t2 = time.time()
    print(str(datetime.timedelta(seconds=t2-t1)))