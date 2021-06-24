# -*- coding: utf-8 -*-
"""
Created on Thu Jun 10 21:40:37 2021

@author: ZhengBin
"""
from PyQt5.QtGui import QImage,QPixmap
from PyQt5.QtWidgets import QDialog,QMessageBox,QGraphicsScene,QGraphicsPixmapItem,QApplication,QTableWidgetItem,QGridLayout,QFileDialog
from src.parameters import Ui_Dialog
from src.dlcrange import Ui_dlc_range
from src.showimage import Ui_image
from src.datapro import is_number
from src.scatter_histogramm import Ui_hist_scatter 
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib as mpl
import matplotlib.pyplot as plt
class tableplus():
    def __init__(self,table):
        self.table = table
    def del_tb_text(self):
        try:
            selected_ranges = self.table.tableWidget.selectedRanges()[0]
            for row in range(selected_ranges.topRow(), selected_ranges.bottomRow() + 1):
                for col in range(selected_ranges.leftColumn(), selected_ranges.rightColumn() + 1):
                    newItem = QTableWidgetItem()
                    self.table.tableWidget.setItem(row, col, newItem)
        except BaseException as e:
            print(e)
            return
    
    def paste_tb_text(self):
        try:
            text = QApplication.clipboard().text()
            lst = text.split('\n')[:-1]
            lst1 = []
            for row in lst:
                lst1.append(row.split('\t'))
            selected_ranges = self.table.tableWidget.selectedRanges()[0]
            for r_i,row in enumerate(range(selected_ranges.topRow(), selected_ranges.topRow()+len(lst))):
                for c_i,col in enumerate(range(selected_ranges.leftColumn(), selected_ranges.leftColumn()+len(lst1[0]))):
                    newItem = QTableWidgetItem(lst1[r_i][c_i])
                    self.table.tableWidget.setItem(row, col, newItem)
        except Exception as e:
            print(e)
            return None
    
    def selected_tb_text(self):
        try:
            text_str = ''
            selected_ranges = self.table.tableWidget.selectedRanges()[0]
            for row in range(selected_ranges.topRow(), selected_ranges.bottomRow()+1):
                row_str = ""
                for col in range(selected_ranges.leftColumn(), selected_ranges.rightColumn()+1):
                    item = self.table.tableWidget.item(row, col)
                    if item == None:
                        row_str += ' ' + '\t'
                    else:
                        row_str += item.text() + '\t'
                text_str += row_str + '\n'
            clipboard = QApplication.clipboard() 
            clipboard.setText(text_str)
            return text_str
        except BaseException as e:
            print(e)
            return None
 
    def copy(self):
        text = self.selected_tb_text()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
 
    def cut(self):
        self.copy()
        self.del_tb_text()
 
    def paste(self):
        self.paste_tb_text()
class para_window(QDialog,Ui_Dialog):
    def __init__(self,pb,myWin):
        super(para_window, self).__init__()
        self.setupUi(self)
        self.pb=pb
        self.myWin = myWin
        self.myWin.allowrotate = False
        self.action_init()
    def action_init(self):
        self.sens.valueChanged.connect(self.spinbox_changevalue)
        self.xlimit.valueChanged.connect(self.spinbox_changevalue)
        self.xsens.valueChanged.connect(self.spinbox_changevalue)
        self.peakH.valueChanged.connect(self.spinbox_changevalue)
        self.highspeed.toggled.connect(self.hispeedcorrect)
        self.spinBox.valueChanged.connect(self.spinbox_changevalue)
        self.lp_min.valueChanged.connect(self.spinbox_changevalue)
        self.lp_max.valueChanged.connect(self.spinbox_changevalue)
        self.rotatestate.setChecked(False)
        self.rotatestate.stateChanged.connect(self.cbchange)
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
        elif sender == self.lp_max:
            self.pb.taskarg['lp'][1] = value
        elif sender == self.lp_min:
            self.pb.taskarg['lp'][0]=value
    def hispeedcorrect(self):
        if self.highspeed.isChecked()==True:
            self.pb.taskarg['highspeed']=True
        else:
            self.pb.taskarg['highspeed']=False
    def cbchange(self):
        sender = self.sender()
        if sender == self.rotatestate:
            self.myWin.allowrotate = not self.myWin.allowrotate
class dlcrange_window(QDialog,Ui_dlc_range):
    def __init__(self,myWin):
        super(dlcrange_window, self).__init__()
        self.setupUi(self)
        self.myWin = myWin
        self.action_init()
    def action_init(self):
        self.pushButton.clicked.connect(self.table_update)
    def table_update(self):
        dic = {}
        for r in range(1,10):
            if None not in [self.tableWidget.item(r, 0),self.tableWidget.item(r, 1),self.tableWidget.item(r, 2)]:
                if is_number(self.tableWidget.item(r, 1).text())and\
                    is_number(self.tableWidget.item(r, 2).text()) and\
                    float(self.tableWidget.item(r, 1).text())<=float(self.tableWidget.item(r, 2).text()) and\
                        float(self.tableWidget.item(r, 1).text())>0:
                    dic[self.tableWidget.item(r, 0).text()] = (float(self.tableWidget.item(r, 1).text()),float(self.tableWidget.item(r, 2).text()))
                else:
                    QMessageBox.information(self,"Erroe","Input error!")
                    return None
        d = np.diff(np.sort(np.array(list(dic.values())),axis=0).reshape(-1))
        if sum(np.where(d<=0)[0])!=0:
            QMessageBox.information(self,"Erroe","Input error!")
            return None
        self.myWin.pb.taskarg['mark'] = dic
        self.close()
class showimage(QDialog,Ui_image):
    def __init__(self):
        super(showimage, self).__init__()
        self.setupUi(self)
    def show_img(self,img):
        if img == None:
            self.close()
            return None
        self.img = img
        scale = img.size[0]/589
        #img = img.resize((int(img.size[0]/scale), int(img.size[1]/scale)),Image.ANTIALIAS)
        #img.show()
        self.frame = QImage(np.array(img), img.size[0], img.size[1], QImage.Format_RGB888)
        self.pix = QPixmap.fromImage(self.frame).scaledToWidth(int(img.size[0]/scale)).scaledToHeight(int(img.size[1]/scale))
        self.item = QGraphicsPixmapItem(self.pix)
        self.scene = QGraphicsScene()  # 创建场景
        self.scene.addItem(self.item)
        self.graphicsView.setScene(self.scene)
        self.show()
class scatterFigure(FigureCanvas):
    def __init__(self):
        #self.figure = mpl.figure.Figure()
        self.canvas = FigureCanvas(mpl.figure.Figure(dpi=100))
        #self.figure = self.canvas.figure
        self.ax = self.canvas.figure.add_subplot(4,1,(2,4))
        self.ax0 = self.canvas.figure.add_subplot(4,1,(1,1))
        
        plt.subplots_adjust(left=0.3, bottom=0.2, right=0.9, top=0.9,hspace=0,wspace=0)
        #self.figure.patch.set_facecolor('None')
        #self.figure.patch.set_alpha(0)
        self.index = 0
        self.content = {'curve': [],
                        'peak': [],
                        'bottom': [],
                        'mark': [],
                        'fitcurve': [],
                        'k':[],
                        'selrange':[]}
        self.range_fix = False
        self.s = []
        self.h = []
        super(scatterFigure, self).__init__(self.canvas.figure)
    def plotscatter(self,arr_dic,index):
        for s in self.s:
            s.remove()
        self.s = []
        x = [v[0] for i,v in arr_dic.items() if i!=index]
        y = [v[1] for i,v in arr_dic.items() if i!=index]
        if 0 not in [len(x),len(y)]:
            arr_x = np.hstack(x)
            arr_y = np.hstack(y)
            self.s.append(self.ax.scatter(arr_x,arr_y,c='k'))
        x = [v[0] for i,v in arr_dic.items() if i==index]
        y = [v[1] for i,v in arr_dic.items() if i==index]
        if 0 not in [len(x),len(y)]:
            arr_x = np.hstack(x)
            arr_y = np.hstack(y)
            self.s.append(self.ax.scatter(arr_x,arr_y,c='r'))
    def plothisto(self,arr_dic):
        for h in self.h:
            h.remove()
        x = [v[0] for i,v in arr_dic.items()]
        if 0 not in [len(x)]:
            arr_x = np.hstack(x)
            self.s.append(self.ax0.hist(arr_x,bins=10)[-1])
    def clean(self):
        for l in self.ax.lines:
            l.remove()
class statistics_win(QDialog,Ui_hist_scatter):
    def __init__(self,myWin):
        super(statistics_win, self).__init__()
        self.myWin = myWin
        self.setupUi(self)
        self.F = scatterFigure()
        self.horizontalLayout_2.addWidget(self.F.canvas)
        self.force_index = 0
        self.arr_dic = {}
        self.displace()
        self.action_init()
    def action_init(self):
        self.pushButton.clicked.connect(self.delete)
        self.pushButton_4.clicked.connect(self.plot)
        self.pushButton_5.clicked.connect(self.save)
        self.pushButton_6.clicked.connect(self.openfile)
    def displace(self):
        self.F.clean()
        self.horizontalLayout_2.removeWidget(self.F.canvas)
        self.F.canvas.draw()
        self.horizontalLayout_2.addWidget(self.F.canvas)
    def get_data(self):
        if not self.myWin.pb.state and self.myWin.pb.tasktype!='smfs':
            return None
        fc = self.myWin.pb.fc
        ljp = self.myWin.pb.ljp
        self.force_index = self.myWin.pb.forcecurve_index
        fc.recover_force(ljp)
        data = fc.get_prodata()['retract']
        data_y = data['vDeflection'].reshape(-1)*1e12
        force_arr = data_y[fc.data['peakindex'][:-1]]
        print(force_arr)
        dlc_arr = fc.data['dlc']
        print(dlc_arr)
        self.arr_dic[self.force_index] = (dlc_arr,force_arr)
        fc.clean_force()
        self.fname = 'test.scatterplot'
    def plot(self):
        if not self.myWin.pb.state or self.myWin.pb.tasktype!='smfs':
            return None
        self.get_data()
        self.F.plotscatter(self.arr_dic,self.force_index)
        self.F.plothisto(self.arr_dic)
        self.displace()
    def delete(self):
        self.force_index = self.myWin.pb.forcecurve_index
        if self.force_index in self.arr_dic.keys():
            del self.arr_dic[self.force_index]
        self.F.plotscatter(self.arr_dic,self.force_index)
        self.F.plothisto(self.arr_dic)
        self.displace()
    def save(self):
        import os
        import pickle
        if not self.myWin.pb.state or self.myWin.pb.tasktype!='smfs':
            return None
        fname = self.myWin.pb.zpo.fname
        todir = os.path.dirname(fname)
        basename = os.path.basename(fname)
        rawname = os.path.splitext(basename)[0]
        fname = os.path.join(todir,"{}.{}".format(rawname,'scatterplot'))
        with open(fname,'wb') as f:
            data = dict(arr_dic=self.arr_dic)
            pickle.dump(data,f)
    def openfile(self):
        import os
        import pickle
        if not self.myWin.pb.state or self.myWin.pb.tasktype!='smfs':
            return None
        fname = self.myWin.pb.zpo.fname
        todir = os.path.dirname(fname)
        basename = os.path.basename(fname)
        rawname = os.path.splitext(basename)[0]
        fname = os.path.join(todir,"{}.{}".format(rawname,'scatterplot'))
        if os.path.isfile(fname):
            pass
        else:
            fname, _ = QFileDialog.getOpenFileName(self, "Open Scatter Plot", '*.scatterplot')
        if os.path.isfile(fname):
            with open(fname,'rb') as f:
                data = pickle.load(f)
                self.arr_dic = data['arr_dic']
            self.F.plotscatter(self.arr_dic,self.force_index)
            self.F.plothisto(self.arr_dic)
            self.displace()
        pass