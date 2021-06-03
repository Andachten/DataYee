import time
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox
import numpy as np
import copy
import os
import pickle
from src.loadjpk import forcecurve,loadjpkfile,zipfileopera
from src.datapro_new import noise_down,cal_baseline_drift,cal_baseline_x,cal_baseline_y,\
    cal_highspeed_drift,predict,findpeak,wlcfit,peakH,peakN,slope,countdlc,mkbaseondlc
from src.datapro_new import Lc_transformer,plotmap,plothist,findpeak_smallrange
func_lst = [noise_down,cal_baseline_drift,cal_baseline_y,cal_baseline_x,\
    cal_highspeed_drift,predict,findpeak,peakH,wlcfit,peakN,slope,countdlc,mkbaseondlc]
def process_customize(fc,functions=[0]):
    for i in functions:
        func_lst[i](fc)
def main_smfs(fc,zpo):
    if fc.data['rawdata'] == {}:
        return None
    fc.data['tasktype']='smfs'
    process_customize(fc,[0,2,3,4,6,7,8,9,10,11,12])
    if not fc.data['peaknum_judge']:
        return None
    if fc.data['arg']['usemodel']:
        process_customize(fc, [5])
    if not fc.data['mobilenet_judge']:
        return None
    fc.clean_force()
    zpo.changingforce(fc)
def main_cell(fc,zpo):
    if fc.data['rawdata'] == {} or fc.data['rawdata']['retract']['vDeflection'].sum()==0:
        return None
    fc.data['tasktype']='cell_curve'
    process_customize(fc, [0,1,2,3,4,6,9,10])
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
        self.highspeedcorr = np.array([])
        self.taskarg = {'peakH': 30,
           'sens': 10,
           'peakN': [1, 6],
           'xlim': 20,
           'lp': (0.34, 0.38),
           'mark': {'GB1': (13, 23), 'I27': (23, 36)},
           'fitjudge': False,
           'usemodel':True,
           'xsens':2,
           'highspeed':False,
           'modelstrict':False}
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
    def pk_indexchange(self,n,coor=(None,None)):
        if not self.state:
            return None
        peaklength = len(self.fc.data['peakindex'])
        if peaklength == 0:
            return None
        if n==None and coor[0]!=None and coor[1]!=None:
            datax,datay=coor
            self.fc.recover_force(self.ljp)
            data = self.fc.get_prodata()['retract']
            data_x,data_y = data['measuredHeight'].reshape(-1)*1e9,data['vDeflection'].reshape(-1)*1e12
            index = np.argmin(np.abs(data_x[np.argmin(np.abs(datax-data_x))]-data_x[self.fc.data['peakindex']]))
            self.forcepeak_index=index
            self.fc.clean_force()
            return True
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
        if self.tasktype == 'smfs':
            if 'retract' not in self.fc.data['rawdata'].keys():
                self.fc.recover_force(self.ljp)
            self.fc.data['arg'] = self.taskarg
            cal_baseline_x(self.fc)
            process_customize(self.fc,range(6,13))
        self.curve_change()
    def pk_delete(self):
        if not self.state:
            return None
        if len(self.fc.data['peakindex'])>0:
            del self.fc.data['peakindex'][self.forcepeak_index]
            del self.fc.data['k'][self.forcepeak_index]
        if self.tasktype == 'smfs' and len(self.fc.data['wlcarg'])>0 :
            del self.fc.data['wlcarg'][self.forcepeak_index]
            process_customize(self.fc,[11,12])
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
        process_customize(self.fc,[11,12])
        self.curve_change()
    def lc_change(self,dlc=0,amply=1):
        if len(self.fc.data['wlcarg'])==0:
            return None
        self.fc.data['arg'] = self.taskarg
        real_peakindex = np.argwhere(self.zpo[self.forcecurve_index]['peakindex']==self.fc.data['peakindex'][self.forcepeak_index])[0][0]
        self.fc.data['wlcarg'][self.forcepeak_index]=(self.zpo[self.forcecurve_index]['wlcarg'][real_peakindex][0]+amply*dlc,
                                                 self.fc.data['wlcarg'][self.forcepeak_index][1])
        process_customize(self.fc,[11,12])
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
        res_index = self.fc.data['peakindex'][self.forcepeak_index]+value
        if res_index<=0 or res_index>=max(self.fc.data['peakindex']):
            return None
        if self.forcepeak_index+1<len(self.fc.data['peakindex']) and res_index>self.fc.data['peakindex'][self.forcepeak_index+1]:
            return None
        self.fc.data['peakindex'][self.forcepeak_index]=res_index
        if self.fc.data['tasktype']=='smfs':
            process_customize(self.fc,[8,10,11,12])
        elif self.fc.data['tasktype']=='cell_curve':
            process_customize(self.fc,[9,10])
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
            process_customize(self.fc,[6,7,8,9,10,11,12])
        elif self.tasktype == 'cell_curve':
            process_customize(self.fc,[6,9,10])
        self.fc.data['artificial_judge'] = True
        self.fc.clean_force()
        self.curve_change()
        self.zpo.changedforce()
        self.change_dic={}
    def savechange(self,name,saveas=False):
        if not self.state:
            return None
        self.change_dic={}
        self.zpo.changedforce(name,saveas)
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
        if self.forcepeak_index>len(self.fc.data['peakindex'])-1:
            self.forcepeak_index = len(self.fc.data['peakindex'])-1
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
    def copypeak_(self):
        if not self.state:
            return None
        if len(self.fc.data['peakindex'])==0:
            return None
        self.fc.recover_force(self.ljp)
        data = self.fc.get_prodata()['retract']
        data_x,data_y = data['measuredHeight'].reshape(-1)*1e9,data['vDeflection'].reshape(-1)*1e12
        if self.forcepeak_index==0:
            index = np.where(data_x<data_x[self.fc.data['peakindex'][self.forcepeak_index]]-self.taskarg['xsens'])[0]
        else:
            index = np.where((data_x<data_x[self.fc.data['peakindex'][self.forcepeak_index]]-self.taskarg['xsens'])&(data_x>data_x[self.fc.data['peakindex'][self.forcepeak_index-1]]+self.taskarg['xsens']))[0]
        p = findpeak_smallrange(data_y[index])
        if len(p)==0:
            v=index[-1]-1
        else:
            v=index[0]+p[-1]
        if self.forcepeak_index>=0 and self.tasktype=='smfs':
            self.fc.data['peakindex'].insert(self.forcepeak_index,v)
            process_customize(self.fc,[8,10,11,12])
            self.fc.clean_force()
            self.curve_change()
            self.zpo.changedforce()
            self.change_dic={}
        self.fc.clean_force()
    def copypeak(self,xdata,ydata):
        if not self.state:
            return None
        self.fc.recover_force(self.ljp)
        data = self.fc.get_prodata()['retract']
        data_x,data_y = data['measuredHeight'].reshape(-1)*1e9,data['vDeflection'].reshape(-1)*1e12
        index = np.argmin(np.abs(data_x-xdata))
        i = len(np.where(self.fc.data['peakindex']<index)[0])
        if self.forcepeak_index>=0:
            self.fc.data['peakindex'].insert(i,index)
        if  self.fc.data['tasktype']=='smfs':
            process_customize(self.fc,[8,10,11,12])
        elif self.fc.data['tasktype']=='cell_curve':
            process_customize(self.fc,[9,10])
        self.fc.clean_force()
        self.curve_change()
        self.zpo.changedforce()
        self.change_dic={}
        self.forcepeak_index=i
        self.fc.clean_force()
    def export_prodata(self,sel):
        if not self.state:
            return None
        if self.tasktype == 'cell_curve':
            T = self.zpo.export_celldata(self.ljp)
        elif self.tasktype == 'smfs':
            T = self.zpo.get_arg(self.ljp)
            #T = self.zpo.extrac_argdata(self.ljp)
        if not T:
            QMessageBox.information(sel,"Warning","Failed!")
    def exporttxt(self):
        if not self.state:
            return None
        if self.tasktype == 'cell_curve':
            self.zpo.exporttxt(self.ljp,self.forcecurve_index)
        elif self.tasktype == 'smfs':
            self.zpo.exporttxt(self.ljp,self.forcecurve_index)
    def exportbatchtxt(self):
        if not self.state:
            return None
        for i in range(self.forcecurve_index+1):
            self.zpo.exporttxt(self.ljp,i)
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
        self.highspeedcorr = np.array([])
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
                self.change={}
                self.ready_run = True
                break
            self.fc.data = data
            self.fc.data['arg'] = self.taskarg
            main(self.fc,self.zpo,self.tasktype)
            if self.taskarg['highspeed'] and self.fc.data['offset']['highspeed']>0:
                self.highspeedcorr=np.append(self.highspeedcorr,self.fc.data['offset']['highspeed'])
        else:
            if self.taskarg['highspeed'] and len(self.highspeedcorr)!=0:
                for k,v in self.zpo.change.items():
                    self.zpo.change[k].data['offset']['highspeed']=self.highspeedcorr.mean()
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