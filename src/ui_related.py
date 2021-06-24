# -*- coding: utf-8 -*-
"""
Created on Thu Jun 10 21:40:37 2021

@author: ZhengBin
"""
from PyQt5.QtGui import QImage,QPixmap
from PyQt5.QtWidgets import QDialog,QMessageBox,QGraphicsScene,QGraphicsPixmapItem,QApplication,QTableWidgetItem
from src.parameters import Ui_Dialog
from src.dlcrange import Ui_dlc_range
from src.showimage import Ui_image
from src.datapro import is_number
from src.scatter_histogramm import Ui_hist_scatter
import numpy as np
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
class statistics_hist_scatter(QDialog,Ui_hist_scatter):
    def __init__(self,myWin):
        super(statistics_hist_scatter, self).__init__()
        self.setupUi(self)
        self.myWin = myWin
        self.action_init()
    def action_init(self):
        pass