import sys
import copy


import numpy as np
from src.datapro import lcfunc
from src.loadjpk import forcecurve, loadjpkfile
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QProgressDialog, QGridLayout, \
    QButtonGroup,QDialog
from src.designer import Ui_MainWindow
from src.parameters import Ui_Dialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from src.main_new import programbody
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.style as mplstyle

mplstyle.use('fast')
mpl.rcParams['font.family'] = 'Arial'
mpl.rcParams['axes.labelsize'] = 16
mpl.rcParams['axes.labelweight'] = 'normal'
mpl.rcParams['axes.linewidth'] = 1
mpl.rcParams['font.size'] = 12
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.spines.top'] = False
mpl.rcParams['figure.subplot.left'] = 0.05
mpl.rcParams['figure.subplot.right'] = 1
color_lsts = ['#f76707']*9


# plt.ion()
def getfitcurve(wlcarg, peakindex, data_x):
    arg_lst = []
    for i, arg in enumerate(wlcarg):
        x_ = np.linspace(0, data_x[peakindex[i]] + 10)
        y_ = lcfunc(x_, *arg)
        x_ = x_[:y_.argmax()]
        y_ = y_[:y_.argmax()]
        arg_lst.append((x_, y_))
    return arg_lst


class myFigure(FigureCanvas):
    def __init__(self):
        self.figure = plt.figure()
        self.ax = self.figure.add_subplot(111)
        self.ax.plot([-1e4, 1e4], [0, 0], lw=1.5, c='#ff8787')
        self.ax.plot([0, 0], [-50, 50], 'r-', lw=1)
        self.figure.patch.set_facecolor('None')
        self.figure.patch.set_alpha(0)
        self.fc_old = forcecurve()
        self.fc_new = forcecurve()
        self.index = 0
        self.content = {'curve': [],
                        'peak': [],
                        'bottom': [],
                        'mark': [],
                        'fitcurve': [],
                        'k':[]}
        super(myFigure, self).__init__(self.figure)

    def getdata(self):
        data = self.fc_new.get_prodata()['retract']
        self.data_y = data['vDeflection'][:, 0] * 1e12
        self.data_x = data['measuredHeight'][:, 0] * 1e9

    def setlim(self, xlim, ylim):
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

    def plotcurve(self):
        for line in self.content['curve']:
            line[0].remove()
        self.content['curve'] = []
        self.fc_new.recover_force(self.ljp)
        # self.ax.set_yticks(np.arange(0,self.data_y.max(),150))
        if not self.fc_new.data['artificial_judge']:
            self.content['curve'].append(self.ax.plot(self.data_x, self.data_y, 'b', lw=1.5))
        else:
            self.content['curve'].append(self.ax.plot(self.data_x, self.data_y, c='#495057', lw=1.5))

    def plotfitcurve(self):
        for line in self.content['fitcurve']:
            line[0].remove()
        self.content['fitcurve'] = []
        if len(self.fc_new.data['peakindex']) <= 0:
            return None
        data_x = self.fc_new.get_prodata()['retract']['measuredHeight'][:, 0] * 1e9
        fit_lst = getfitcurve(self.fc_new.data['wlcarg'], self.fc_new.data['peakindex'], data_x)
        color_lst = (len(self.fc_new.data['wlcarg']) // len(color_lsts) + 1) * color_lsts
        for i, xy_ in enumerate(fit_lst):
            x_, y_ = xy_
            self.content['fitcurve'].append(self.ax.plot(x_, y_, '-.', c=color_lst[i], lw=1.5))

    def plotpeak(self):
        for line in self.content['peak']:
            line[0].remove()
        self.content['peak'] = []
        peak_index = self.fc_new.data['peakindex']
        if len(peak_index) <= 0:
            return None
        
        
        self.content['peak'].append(
            (self.ax.plot(self.data_x[peak_index], self.data_y[peak_index], 'yo', markersize=8)))
        self.content['peak'].append(
            self.ax.plot(self.data_x[peak_index[self.index]], self.data_y[peak_index[self.index]],'ro', markersize=8))
        '''
    def plotbottom(self):
        for line in self.content['bottom']:
            line[0].remove()
        self.content['bottom'] = []
        bottom_index = self.fc_new.data['bottomindex']
        if len(bottom_index) <= 0:
            return None
        self.content['bottom'].append(
            self.ax.plot(self.data_x[bottom_index], self.data_y[bottom_index], 'g*', markersize=8))
        '''
    def plotmark(self):
        for line in self.content['mark']:
            line.remove()
        self.content['mark'] = []
        font = {'family': 'serif', 'style': 'italic', 'weight': 'normal', 'color': 'red', 'size': 14}
        mark = self.fc_new.data['mark']
        if len(mark) <= 0:
            return None
        peak_index = self.fc_new.data['peakindex']
        for i in range(len(mark)):
            if mark[i] == 'none':
                font['color'] = 'red'
            else:
                font['color'] = 'blue'
            if i % 3 == 0:
                self.content['mark'].append(
                    self.ax.text(self.data_x[peak_index[i]] - 3, -70, '{}.{}'.format(i, mark[i]), font,
                                 horizontalalignment='left'))
            elif i % 3 == 1:
                self.content['mark'].append(
                    self.ax.text(self.data_x[peak_index[i]] - 3, -50, '{}.{}'.format(i, mark[i]), font,
                                 horizontalalignment='left'))
            elif i % 3 == 2:
                self.content['mark'].append(
                    self.ax.text(self.data_x[peak_index[i]] - 3, -30, '{}.{}'.format(i, mark[i]), font,
                                 horizontalalignment='left'))
    def plotk(self):
        for line in self.content['k']:
            line[0].remove()
        self.content['k'] = []
        peak_index = self.fc_new.data['peakindex']
        k_lst = self.fc_new.data['k']
        xrange = (self.data_x[peak_index[-1]]-self.data_x[0])*0.04
        yrange = (self.data_y.max()-self.data_y.min())*0.08
        for i,p_i in enumerate(peak_index):
            x,y = self.data_x[p_i],self.data_y[p_i]
            b = y - k_lst[i]*x
            x_ = np.linspace(x-xrange,x+xrange)
            y_ = k_lst[i]*x_+b
            xyrange_index = np.where((y_<y+yrange)&(y_>y-yrange))[0]
            x_ = x_[xyrange_index]
            y_ = y_[xyrange_index]
            self.content['k'].append(self.ax.plot(x_,y_,'b',lw=1))
    def changeall(self):
        self.plotcurve()
        if len(self.fc_new.data['peakindex']) > 0:
            self.setlim((-10, self.data_x[self.fc_new.data['peakindex'][-1]] + 30), (-90, self.data_y.max() + 40))
        else:
            self.setlim((-10, self.data_x.max() + 30), (-90, self.data_y.max() + 40))
        self.plotfitcurve()
        self.plotpeak()
        #self.plotbottom()
        self.plotmark()
        self.plotk()

    def plot(self, fc, index, ljp, tasktype='smfs'):
        self.ljp = ljp
        self.fc_new = fc
        if 'rawdata' not in self.fc_new.data.keys() or 'retract' not in self.fc_new.data['rawdata'].keys():
            self.fc_new.recover_force(ljp)
        self.getdata()
        if self.index != index:
            self.index = index
            self.plotpeak()
        if self.fc_new.data['datamsg'] != self.fc_old.data['datamsg']:
            self.changeall()
        elif self.fc_new.data['artificial_judge'] != self.fc_old.data['artificial_judge']:
            self.changeall()
        elif self.fc_new.data['offset'] != self.fc_old.data['offset']:
            self.changeall()
        else:
            if self.fc_new.data['peakindex'] != self.fc_old.data['peakindex']:
                self.plotpeak()
            if self.fc_new.data['artificial_judge'] != self.fc_old.data['artificial_judge']:
                self.plotcurve()
            if self.fc_new.data['wlcarg'] != self.fc_old.data['wlcarg']:
                self.plotfitcurve()
            if self.fc_new.data['mark'] != self.fc_old.data['mark']:
                self.plotmark()
            if self.fc_new.data['k'] != self.fc_old.data['k']:
                self.plotk()
        if tasktype == 'cell_curve':
            set_range = 0.1
            ylim_min = self.data_y[int(set_range*len(self.data_y)):].min()-20
            self.setlim((self.data_x.min()-20, self.data_x.max() + 0.1*(self.data_x.max()-self.data_x.min())), (ylim_min, self.data_y.max() + 10))
        plt.draw()
        self.fc_old = copy.deepcopy(self.fc_new)
class para_window(QDialog,Ui_Dialog):
    def __init__(self,pb,myWin):
        super(para_window, self).__init__()
        self.setupUi(self)
        self.pb=pb
        self.myWin = myWin
        self.action_init()
    def action_init(self):
        self.sens.valueChanged.connect(self.spinbox_changevalue)
        self.xlimit.valueChanged.connect(self.spinbox_changevalue)
        self.xsens.valueChanged.connect(self.spinbox_changevalue)
        self.peakH.valueChanged.connect(self.spinbox_changevalue)
        self.highspeed.toggled.connect(self.hispeedcorrect)
        self.spinBox.valueChanged.connect(self.spinbox_changevalue)
        pass
    def spinbox_changevalue(self, value):
        sender = self.sender()
        if sender == self.sens:
            self.pb.taskarg['sens'] = value
        elif sender == self.xlimit:
            self.pb.taskarg['xlim'] = value
        elif sender == self.xsens:
            self.pb.taskarg['xsens'] = value
        elif sender == self.peakH:
            self.pb.taskarg['peakH'] = value
        elif sender == self.spinBox:
            self.myWin.siglestep = value
    def hispeedcorrect(self):
        if self.highspeed.isChecked()==True:
            self.pb.taskarg['highspeed']=True
        else:
            self.pb.taskarg['highspeed']=False
        print(self.pb.taskarg)


class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.filedir = ''
        self.fname = ''
        self.tasktype = 'smfs'
        self.svfname = 'test.DataYee-force'
        self.pb = programbody()
        # self.run_z = False
        # self.state = False
        # self.change_dict={}
        # self.force_index = 0
        # self.peak_index = 0
        self.F = myFigure()
        self.gridlayout = QGridLayout(self.groupBox)
        self.gridlayout.addWidget(self.F)
        self.action_init()

    def action_init(self):
        self.siglestep = 5
        self.lc_value = self.lcdoubleSpinBox.value()
        self.lp_value = self.lpdoubleSpinBox.value()
        self.k_value = self.kSpinBox.value()
        self.actionForce_Curve.triggered.connect(self.openfile)
        self.actionSave.triggered.connect(self.savefile)
        self.actionSave_as.triggered.connect(self.saveasfile)
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
        self.kSlider.valueChanged[int].connect(self.kslidechange)
        self.lcdoubleSpinBox.valueChanged.connect(self.spinbox_changevalue)
        self.lpdoubleSpinBox.valueChanged.connect(self.spinbox_changevalue)
        self.kSpinBox.valueChanged.connect(self.spinbox_changevalue)
        self.spinBox_2.valueChanged.connect(self.spinbox_changevalue)
        self.spinBox_3.valueChanged.connect(self.spinbox_changevalue)
        self.spinBox.valueChanged.connect(self.spinbox_changevalue)
        self.actionexcel.triggered.connect(self.exportexcel)
        self.actionBaseline_plus.triggered.connect(self.baselineplus)
        self.actionBaseline_minus.triggered.connect(self.baselineminus)
        self.actionHistgram.triggered.connect(self.plot_contourhist)
        self.actionScatter.triggered.connect(self.plot_contourscatter)
        self.actionMap.triggered.connect(self.adhesionmap)
        self.actionHistogram.triggered.connect(self.adhesionhist)
        self.actiontxt.triggered.connect(self.exporttxt)
        self.actionpeakindex_plus.triggered.connect(self.peakvalueplus)
        self.actionpeakindex_minus.triggered.connect(self.peakvalueminus)
        self.actioncopy_peak.triggered.connect(self.copypeak)
        self.actionfigure.triggered.connect(self.export_figure)
        self.setFocusPolicy(Qt.StrongFocus)
        self.bg = QButtonGroup(self)
        self.bg.addButton(self.radioButton_2, 0)
        self.bg.addButton(self.tasktype_cell, 1)
        self.bg.buttonClicked.connect(self.rbclicked)
        self.usemodel_cb.setChecked(True)
        self.usemodel_cb.stateChanged.connect(self.statemodel)
        self.fastmode_cb.stateChanged.connect(self.statemodel)
        self.lineEdit.returnPressed.connect(self.changemark)

    def openfile(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Load force curve", '*.txt;;*.jpk-force;;*.jpk-force-map;;*.spm')
        self.fname = fname
        if fname != '':
            self.pb.creattask(fname)

    def openfile_DataYee(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open DataYee Force", '*.DataYee-force')
        self.fname = fname
        if fname != '':
            self.pb.creattask(fname)
            self.displace_result()
            # self.zpo = zipfileopera(self.fname)

    def opendir(self):
        path = QFileDialog.getExistingDirectory(self, 'Load batch of force curve', '*.*')
        self.filedir = path
        if path != '':
            self.pb.creattask(path)
            # self.ljp = loadjpkfile(self.filedir)
            # self.zpo = zipfileopera()
            # self.run_z = True

    def savefile(self):
        self.svfname = self.pb.zpo.fname
        if self.svfname == 'test.DataYee-force':
            self.svfname, _ = QFileDialog.getSaveFileName(self, 'Save DataYee Force', '*.DataYee-force')
        self.pb.savechange(self.svfname)
        # self.change_dict={}
    def saveasfile(self):
        self.svfname = self.pb.zpo.fname
        self.svfname, _ = QFileDialog.getSaveFileName(self, 'Save DataYee Force', '*.DataYee-force')
        self.pb.savechange(self.svfname,saveas=True)

    def aboutprogramm(self):
        _ = QMessageBox.information(self, 'DataYee', 'Programm Version:0.1', QMessageBox.Ok | QMessageBox.Close,
                                    QMessageBox.Close)

    def displace_result(self):
        self.gridlayout.removeWidget(self.F)
        # plt.close()
        # sip.delete(self.F)
        # self.F = MyFigure()
        self.pb.plot(self.F)
        # self.fc.recover_force(self.ljp)
        # self.F.plot(self.fc,self.peak_index)
        self.pb.drawlabel(self.label, self.lclplabel)
        # self.label.setText('Peak select: {}/{}'.format(self.force_index,len(self.zpo)-1))

        self.gridlayout.addWidget(self.F)

    def indexplus(self):
        self.pb.fc_indexchange(1)
        self.displace_result()
        self.spinBox.setValue(self.pb.forcecurve_index)
        self.resetslide()

    def indexreduct(self):
        self.pb.fc_indexchange(-1)
        self.resetslide()
        self.spinBox.setValue(self.pb.forcecurve_index)
        self.displace_result()

    def peakindexplus(self):
        self.pb.pk_indexchange(1)
        self.resetslide()
        self.displace_result()
    def peakvalueplus(self):
        self.pb.pv_change(self.siglestep)
        self.displace_result()
    def peakvalueminus(self):
        self.pb.pv_change(self.siglestep*-1)
        self.displace_result()

    def peakindexretact(self):
        self.pb.pk_indexchange(-1)
        self.resetslide()
        self.displace_result()

    def peakdelete(self):
        self.pb.pk_delete()
        self.resetslide()
        self.displace_result()

    def forcedelete(self):
        self.pb.fc_delete()
        self.resetslide()
        self.displace_result()

    def reset_delete(self):
        self.pb.reset()
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
    def changemark(self):
        mark = self.lineEdit.text()
        if mark!='':
            self.pb.changemark(mark)
            self.displace_result()
    def lcslidechange(self, value):
        self.lc_value = self.lcdoubleSpinBox.value()
        self.lp_value = self.lpdoubleSpinBox.value()
        self.pb.lc_change(value, self.lc_value)
        self.displace_result()

    def lpslidechange(self, value):
        self.lc_value = self.lcdoubleSpinBox.value()
        self.lp_value = self.lpdoubleSpinBox.value()
        self.pb.lp_change(value, self.lp_value)
        self.displace_result()
    def kslidechange(self,value):
        self.k_value = self.kSpinBox.value()
        self.pb.k_change(value, self.k_value)
        self.displace_result()

    def resetslide(self):
        self.lcslide.setValue(0)
        self.lpslide.setValue(0)
    def plot_contourhist(self):
        self.pb.plot_contourhist()
    def plot_contourscatter(self):
        self.pb.plot_contourscatter()
    def adhesionmap(self):
        self.pb.adhesionmap()
    def adhesionhist(self):
        self.pb.adhesionhist()

    def spinbox_changevalue(self, value):
        sender = self.sender()
        if sender == self.lcdoubleSpinBox:
            self.lc_value = value
        elif sender == self.lpdoubleSpinBox:
            self.lp_value = value
        elif sender == self.kSpinBox:
            self.k_value = value
        elif sender == self.spinBox:
            if value < len(self.pb.zpo):
                self.pb.forcecurve_index = value
            else:
                self.pb.forcecurve_index = len(self.pb.zpo) - 1
            self.displace_result()
        elif sender == self.spinBox_2:
            self.pb.taskarg['peakN'][0] = value
        elif sender == self.spinBox_3:
            self.pb.taskarg['peakN'][1] = value

    def rbclicked(self):
        sender = self.sender()
        if sender == self.bg:
            if self.bg.checkedId() == 0:
                self.tasktype = 'smfs'
            elif self.bg.checkedId() == 1:
                self.tasktype = 'cell_curve'
    def copypeak(self):
        self.pb.copypeak()
    def statemodel(self):
        self.pb.taskarg['usemodel'] = self.usemodel_cb.isChecked()

    def baselineplus(self):
        self.pb.baseline_change(5e-12)
        self.displace_result()

    def baselineminus(self):
        self.pb.baseline_change(-5e-12)
        self.displace_result()

    def exportexcel(self):
        self.pb.export_prodata(self)
    def exporttxt(self):
        self.pb.exporttxt()
    def export_figure(self):
        self.pb.export_figure(self.F.figure)
    def run(self):
        progress = QProgressDialog(self)
        self.pb.tasktype = self.tasktype
        self.pb.execu_autostep(progress, self)
        if self.pb.state:
            self.displace_result()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    child_window = para_window(myWin.pb,myWin)
    myWin.actionparameters_setting.triggered.connect(child_window.show)
    myWin.show()
    sys.exit(app.exec_())
    plt.close()
    