# -*- coding: utf-8 -*-
"""
Created on Sun Apr 11 18:16:38 2021

@author: ZhengBin
"""

import sys
import os
import copy
import time
os.environ['KMP_DUPLICATE_LIB_OK']='True'
import numpy as np
from datapro import lcfunc
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow,QFileDialog,QMessageBox,QProgressDialog,QGridLayout
from designer import Ui_MainWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from loadjpk import loadjpkfile,zipfileopera,forcecurve
from main import process_customize
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['font.family']='Arial'
mpl.rcParams['axes.labelsize']=16
mpl.rcParams['axes.labelweight']='normal'
mpl.rcParams['axes.linewidth']=1
mpl.rcParams['font.size'] = 12
mpl.rcParams['axes.spines.right']=False
mpl.rcParams['axes.spines.top']=False
color_lsts = ['#f76707','#74b816','#f59f00','#1098ad','#ae3ec9','#0ca678','#f03e3e']
plt.ion()
def getfitcurve(wlcarg,peakindex,data_x):
    arg_lst = []
    for i,arg in enumerate(wlcarg):
        x_ = np.linspace(0,data_x[peakindex[i]]+10)
        y_ = lcfunc(x_,*arg)
        x_ = x_[:y_.argmax()]
        y_ = y_[:y_.argmax()]
        arg_lst.append((x_,y_))
    return arg_lst
class MyFigure(FigureCanvas):
    def __init__(self):
        self.figure = plt.figure()
        self.ax = self.figure.add_subplot(111)
        self.ax.plot([-5,15],[0,0],'r-',lw=1.5)
        self.ax.plot([0,0],[-50,50],'r-',lw=1)
        self.figure.patch.set_facecolor('None')
        self.figure.patch.set_alpha(0)
        self.fc = forcecurve()
        self.index = 0
        self.curve_lst = []
        self.peakplot_lst = []
        self.fitcurve_lst = []
        self.k_lst = []
        self.mark_lst = []
        super(MyFigure,self).__init__(self.figure)
    def plot_(self,fc,index):
        data_y = fc.get_prodata()['retract']['vDeflection'][:,0]*1e12
        data_x = fc.get_prodata()['retract']['measuredHeight'][:,0]*1e9
        peak_index = fc.data['peakindex']
        bottom_index = fc.data['bottomindex']
        if fc.data['datamsg']!=self.fc.data['datamsg'] or fc.data['artificial_judge']!= self.fc.data['artificial_judge'] or fc.data['offset']!=self.fc.data['offset']:
            for line in self.curve_lst:
                line[0].remove()
            self.curve_lst = []
            if not fc.data['artificial_judge']:
                self.curve_lst.append(self.ax.plot(data_x,data_y,'b',lw=1.5))
            else:
                self.curve_lst.append(self.ax.plot(data_x,data_y,'k',lw=1.5))
        if fc.data['datamsg']!=self.fc.data['datamsg'] or fc.data['peakindex']!=self.fc.data['peakindex'] or index != self.index or fc.data['offset']!=self.fc.data['offset']:
            for line in self.peakplot_lst:
                line[0].remove()
            self.peakplot_lst = []
            self.index = index
            self.ax.set_xlim([-5,data_x[peak_index[-1]]+40])
            self.ax.set_ylim([-90,data_y.max()+40])
            self.ax.set_yticks(np.arange(0,data_y.max(),150))
            self.peakplot_lst.append(self.ax.plot(data_x[peak_index[self.index]],data_y[peak_index[self.index]],'ro',markersize=16))
            self.peakplot_lst.append((self.ax.plot(data_x[peak_index],data_y[peak_index],'ro',markersize=8)))
            self.peakplot_lst.append(self.ax.plot(data_x[bottom_index],data_y[bottom_index],'g*',markersize=8))
        
        if fc.data['wlcarg']!=self.fc.data['wlcarg'] or fc.data['offset']!=self.fc.data['offset']:
            for line in self.fitcurve_lst:
                line[0].remove()
            self.fitcurve_lst=[]
            fit_lst=getfitcurve(fc.data['wlcarg'],fc.data['peakindex'],data_x)
            color_lst = (len(fc.data['wlcarg'])//len(color_lsts)+1)*color_lsts
            for i,xy_ in enumerate(fit_lst):
                x_,y_ = xy_
                self.fitcurve_lst.append(self.ax.plot(x_,y_,'-.',c=color_lst[i],lw=1.5))
        if fc.data['mark']!=self.fc.data['mark']:
            for text in self.mark_lst:
                text.remove()
            mark = fc.data['mark']
            texts = []
            font={'family':'serif',
                  'style':'italic',
                  'weight':'normal',
                  'color':'red',
                  'size':14
                  }  
            for i in range(len(mark)):
                if mark[i]=='none':
                    font['color'] = 'red'
                else:
                    font['color'] = 'blue'
                if i%3==0:
                    texts.append(self.ax.text(data_x[peak_index[i]]-3,-70,'{}.{}'.format(i,mark[i]),font,horizontalalignment= 'left'))
                elif i%3==1:
                    texts.append(self.ax.text(data_x[peak_index[i]]-3,-50,'{}.{}'.format(i,mark[i]),font,horizontalalignment= 'left'))
                elif i%3==2:
                    texts.append(self.ax.text(data_x[peak_index[i]]-3,-30,'{}.{}'.format(i,mark[i]),font,horizontalalignment= 'left'))
            self.mark_lst = texts
        if fc.data['k']!=self.fc.data['k'] or fc.data['offset']!=self.fc.data['offset']:
            for line in self.k_lst:
                line.remove()
            k_arg = fc.data['k']
            peak_index = fc.data['peakindex']
            for i,p_i in enumerate(k_arg):
                x_ = np.linspace(data_x[p_i]-10,data_x[p_i]+10)
                y_ = np.polyval(k_arg[i],x_)
                self.k_lst.append(self.ax.plot(x_,y_,'b'))
        plt.draw()
        self.fc = copy.deepcopy(fc)
        
class MyMainWindow(QMainWindow,Ui_MainWindow):
    def __init__(self,parent=None):
        super(MyMainWindow,self).__init__(parent)
        self.setupUi(self)
        self.filedir = ''
        self.fname = ''
        self.svfname = 'test.DataYee-force'
        self.run_z = False
        self.change_dict={}
        self.force_index = 0
        self.peak_index = 0
        self.F = MyFigure()
        self.lc_value = self.lcdoubleSpinBox.value()
        self.lp_value = self.lpdoubleSpinBox.value()
        self.gridlayout = QGridLayout(self.groupBox)
        self.gridlayout.addWidget(self.F)
        
        
        self.actionForce_Curve.triggered.connect(self.openfile)
        self.actionSave.triggered.connect(self.savefile)
        self.actionBatch_of_Force_Curve.triggered.connect(self.opendir)
        self.actionDataYee_Force.triggered.connect(self.openfile_DataYee)
        self.actionDataYee.triggered.connect(self.aboutprogramm)
        self.pushButton.clicked.connect(self.run)
        self.downButton.clicked.connect(self.indexplus)
        self.topButton.clicked.connect(self.indexreduct)
        self.leftButton.clicked.connect(self.peakindexretact)
        self.rightButton.clicked.connect(self.peakindexplus)
        self.trashButtom.clicked.connect(self.peakdelete)
        self.actionDelete.triggered.connect(self.forcedelete)
        self.pushButton_2.clicked.connect(self.reset_delete)
        self.lcslide.valueChanged[int].connect(self.lcslidechange)
        self.lpslide.valueChanged[int].connect(self.lpslidechange)
        self.lcdoubleSpinBox.valueChanged.connect(self.spinbox_changevalue)
        self.lpdoubleSpinBox.valueChanged.connect(self.spinbox_changevalue)
        self.spinBox.valueChanged.connect(self.spinbox_changevalue)
        self.actionexcel.triggered.connect(self.exportexcel)
        self.actionBaseline_plus.triggered.connect(self.baselineplus)
        self.actionBaseline_minus.triggered.connect(self.baselineminus)
        self.setFocusPolicy(Qt.StrongFocus)
    def openfile(self):
        fname,_ = QFileDialog.getOpenFileName(self, "Load force curve",'*.txt;;*.jpk-force;;*.jpk-force-map')
        self.fname = fname
        if fname !='':
            self.ljp = loadjpkfile(self.fname)
            self.zpo = zipfileopera()
            self.run_z = True
    def openfile_DataYee(self):
        fname,_ = QFileDialog.getOpenFileName(self, "Open DataYee Force",'*.DataYee-force')
        self.fname = fname
        if fname != '' :
            self.zpo = zipfileopera(self.fname)
            if os.path.isdir(self.zpo.get_sourcepath()):
                self.ljp = loadjpkfile(self.zpo.get_sourcepath())
                self.force_index = 0
                self.peak_index = 0
                self.fc = forcecurve()
                self.fc.data = self.zpo[self.force_index]
                self.displace_result()
    def opendir(self):
        path = QFileDialog.getExistingDirectory(self,'Load batch of force curve','*.*')
        self.filedir = path
        if path != '':
            self.ljp = loadjpkfile(self.filedir)
            self.zpo = zipfileopera()
            self.run_z = True
    def savefile(self):
        self.svfname = self.zpo.fname
        if self.svfname == 'test.DataYee-force':
            self.svfname,_ = QFileDialog.getSaveFileName(self,'Save DataYee Force','*.DataYee-force')
        else:
            self.zpo.changedforce(self.svfname)
        if self.svfname == 'test.DataYee-force':
            self.zpo.changedforce()
        else:
            self.zpo.changedforce(self.svfname)
        self.change_dict={}
    def aboutprogramm(self):
        _ = QMessageBox.information(self,'DataYee','Programm Version:0.1', QMessageBox.Ok | QMessageBox.Close, QMessageBox.Close)
    def displace_result(self):
        self.gridlayout.removeWidget(self.F)
        #plt.close()
        #sip.delete(self.F)
        #self.F = MyFigure()
        if self.force_index in self.change_dict.keys():
            self.fc.data = copy.deepcopy(self.zpo.change[self.change_dict[self.force_index]].data)
        else:
            self.fc.data = self.zpo[self.force_index]
        self.fc.recover_force(self.ljp)
        self.F.plot_(self.fc,self.peak_index)
        self.label.setText('Peak select: {}/{}'.format(self.force_index,len(self.zpo)-1))
        if self.peak_index<len(self.fc.data['peakindex'])-1:
            self.lclplabel.setText('Lc={:.1f}nm; lp={:.2f}; dLc={:.1f}nm'.format(*self.fc.data['wlcarg'][self.peak_index],self.fc.data['dlc'][self.peak_index]))
        else:
            self.lclplabel.setText('Lc={:.1f}nm; lp={:.2f}'.format(*self.fc.data['wlcarg'][self.peak_index]))
        self.gridlayout.addWidget(self.F)
    def indexplus(self):
        if self.force_index+1<len(self.zpo):
            self.force_index+=1
            self.peak_index = 0
            self.spinBox.setValue(self.force_index)
            self.resetslide()
            self.displace_result()
    def indexreduct(self):
        if self.force_index-1>=0 and self.force_index-1<len(self.zpo):
            self.force_index-=1
            self.peak_index = 0
            self.spinBox.setValue(self.force_index)
            self.resetslide()
            self.displace_result()
    def peakindexplus(self):
        if self.peak_index + 1<len(self.fc.data['peakindex']):
            self.peak_index+=1
            self.resetslide()
            self.displace_result()
    def peakindexretact(self):
        if self.peak_index-1>=0 and self.peak_index-1<len(self.fc.data['peakindex']):
            self.peak_index-=1
            #self.resetslidevalue()
            self.resetslide()
            self.displace_result()
    def peakdelete(self):
        self.setFocusPolicy(Qt.StrongFocus)
        del self.fc.data['peakindex'][self.peak_index]
        del self.fc.data['bottomindex'][self.peak_index]
        del self.fc.data['wlcarg'][self.peak_index]
        process_customize(self.fc,[6,7])
        self.change_dict[self.force_index] = self.fc.data['datamsg']
        if self.peak_index>=len(self.fc.data['peakindex']):
            self.peak_index = len(self.fc.data['peakindex'])-1
        self.zpo.changingforce(self.fc)
        self.resetslide()
        self.displace_result()
    def forcedelete(self):
        self.fc.data['artificial_judge']=False
        self.change_dict[self.force_index] = self.fc.data['datamsg']
        self.zpo.changingforce(self.fc)
        self.resetslide()
        self.displace_result()
    def reset_delete(self):
        self.setFocusPolicy(Qt.StrongFocus)
        process_customize(self.fc,list(range(2,8)))
        self.fc.data['artificial_judge'] = True
        self.zpo.changingforce(self.fc)
        self.change_dict[self.force_index]=self.fc.data['datamsg']
        self.displace_result()
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Up:
            self.indexreduct()
        elif e.key() == Qt.Key_Down:
            self.indexplus()
        elif e.key() == Qt.Key_Left:
            self.peakindexretact()
        elif e.key() == Qt.Key_Right:
            self.peakindexplus()
        elif e.key() == Qt.Key_Delete:
            self.peakdelete()
    def resetslidevalue(self):
        self.lcslide.setValue(0)
        self.lpslide.setValue(0)
        
    def lcslidechange(self,value):
        self.lc_value = self.lcdoubleSpinBox.value()
        self.lp_value = self.lpdoubleSpinBox.value()
        real_peakindex = np.argwhere(self.zpo[self.force_index]['peakindex']==self.fc.data['peakindex'][self.peak_index])[0][0]
        self.fc.data['wlcarg'][self.peak_index]=(self.zpo[self.force_index]['wlcarg'][real_peakindex][0]+value*self.lc_value,
                                                 self.fc.data['wlcarg'][self.peak_index][1])
        process_customize(self.fc,[6,7])
        self.zpo.changingforce(self.fc)
        self.change_dict[self.force_index] = self.fc.data['datamsg']
        self.displace_result()
    def lpslidechange(self,value):
        self.lc_value = self.lcdoubleSpinBox.value()
        self.lp_value = self.lpdoubleSpinBox.value()
        real_peakindex = np.argwhere(self.zpo[self.force_index]['peakindex']==self.fc.data['peakindex'][self.peak_index])[0][0]
        self.fc.data['wlcarg'][self.peak_index]=(self.fc.data['wlcarg'][self.peak_index][0],
                                                 self.zpo[self.force_index]['wlcarg'][real_peakindex][1]+value*self.lp_value)
        process_customize(self.fc,[6,7])
        self.zpo.changingforce(self.fc)
        self.change_dict[self.force_index] = self.fc.data['datamsg']
        self.displace_result()
    def resetslide(self):
        self.lcslide.setValue(0)
        self.lpslide.setValue(0)
    def spinbox_changevalue(self,value):
        sender = self.sender()
        if sender == self.lcdoubleSpinBox:
            self.lc_value = value
        elif sender == self.lpdoubleSpinBox:
            self.lp_value = value
        elif sender == self.spinBox:
            if value < len(self.zpo):
                self.force_index = value
            else:
                self.force_index = len(self.zpo)-1
            self.displace_result()
    def baselineplus(self):
        self.fc.data['offset']['y']+=5e-12
        process_customize(self.fc,range(4,8))
        self.zpo.changingforce(self.fc)
        self.change_dict[self.force_index] = self.fc.data['datamsg']
        self.displace_result()
    def baselineminus(self):
        self.fc.data['offset']['y']-=5e-12
        self.zpo.changingforce(self.fc)
        process_customize(self.fc,range(4,8))
        self.zpo.changingforce(self.fc)
        self.change_dict[self.force_index] = self.fc.data['datamsg']
        self.displace_result()
    def exportexcel(self):
        self.zpo.extrac_argdata(self.ljp)
    def run(self):
        if not self.run_z:
            return None
        num = len(self.ljp)
        progress = QProgressDialog(self)
        progress.setWindowTitle("Please Wait")  
        progress.setLabelText("Processing...")
        progress.setCancelButtonText("Cancel")
        progress.setMinimumDuration(5)
        progress.setWindowModality(Qt.WindowModal)
        progress.setRange(0,num) 
        self.fc = forcecurve()
        t1 =time.time()
        for i,data in enumerate(self.ljp):
            progress.setValue(i) 
            if progress.wasCanceled():
                QMessageBox.warning(self,"Warning!","Failed!") 
                self.zpo.delet_dataYee()
                break
            if data['rawdata']=={}:
                continue
            
            self.fc.data = data
            process_customize(self.fc,[0,2,3,4,5,6,7,8])
            
            if not self.fc.data['peaknum_judge']:
                continue
            process_customize(self.fc,[1])
            if not self.fc.data['mobilenet_judge']:
                continue
            self.zpo.addforce(self.fc)
        else:
            progress.setValue(num)
            t2=time.time()
            print((t2-t1)/i,t2-t1,i)
            QMessageBox.information(self,"Notic","Success")
            self.run_z = False
            self.peak_index = 0
            self.force_index = 0
            self.displace_result()
if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    myWin.show()
    sys.exit(app.exec_())
    plt.close()