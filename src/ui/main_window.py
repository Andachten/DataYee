from typing import Any, Optional, TYPE_CHECKING
import sys
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QProgressDialog, QGridLayout, QButtonGroup

if TYPE_CHECKING:
    from src.ui.widgets.force_curve_canvas import ForceCurveCanvas
    from src.main import programbody
    from src.multiProcess import multi_run

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle

mplstyle.use('fast')
mpl.rcParams['path.simplify_threshold'] = 1.0
mpl.rcParams['font.family'] = 'Arial'
mpl.rcParams['axes.labelsize'] = 16
mpl.rcParams['axes.labelweight'] = 'normal'
mpl.rcParams['axes.linewidth'] = 1.5
mpl.rcParams['font.size'] = 12
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.spines.top'] = False
mpl.rcParams['figure.subplot.left'] = 0.05
mpl.rcParams['figure.subplot.right'] = 1
mpl.rcParams['figure.subplot.top'] = 1
mpl.rcParams['figure.subplot.bottom'] = 0.05


class MyMainWindow(QMainWindow):
    """Main DataYee application window."""

    def __init__(self, m_run: 'multi_run', parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        from src.designer import Ui_MainWindow
        self.setupUi(self)
        self.filedir = ''
        self.fname = ''
        self.tasktype = 'smfs'
        self.svfname = 'test.DataYee-force'
        self.pb: 'programbody' = m_run.pb
        self.F: 'ForceCurveCanvas' = m_run.F
        self.gridlayout = QGridLayout(self.groupBox)
        self.gridlayout.addWidget(self.F.canvas)
        self.xdata: Optional[float] = None
        self.xdata_r: Optional[float] = None
        self.ydata: Optional[float] = None
        self.ydata_r: Optional[float] = None
        self.zoomx_state: bool = True
        self.zoomy_state: bool = True
        self.zoomfix_state: bool = False
        self.press: bool = False
        self.control: bool = False
        self.alt: bool = False
        self.img: Any = None
        self.allowrotate: bool = False
        self.overlaymode: bool = False
        self.showimage_win = m_run.showimage_win
        self.fitEnergy = m_run.fitEnergy
        self.action_init()
        self.m_run = m_run

    def setupUi(self, MainWindow: QMainWindow) -> None:
        from src.designer import Ui_MainWindow
        Ui_MainWindow.setupUi(self, MainWindow)

    def action_init(self) -> None:
        self.F.canvas.mpl_connect("button_press_event", self.on_press)
        self.F.canvas.mpl_connect('scroll_event', self.scroll_event)
        self.F.canvas.mpl_connect('motion_notify_event', self.onmotion_event)
        self.F.canvas.mpl_connect("button_release_event", self.on_release)
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
        self.actionbatch_of_txt.triggered.connect(self.exportbatchtxt)
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
        self.stickmodel.setChecked(False)
        self.stickmodel.stateChanged.connect(self.statemodel)
        self.fastmode.setChecked(False)
        self.fastmode.stateChanged.connect(self.statemodel)
        self.lineEdit.returnPressed.connect(self.changemark)
        self.zoomx.setChecked(self.zoomx_state)
        self.zoomy.setChecked(self.zoomy_state)
        self.zoomfix.setChecked(self.zoomfix_state)
        self.zoomx.stateChanged.connect(self.choose_zoom)
        self.zoomy.stateChanged.connect(self.choose_zoom)
        self.zoomfix.stateChanged.connect(self.choose_zoom)
        self.comboBox.currentIndexChanged[str].connect(self.comboBoxchange)
        self.actionBell_Evans.triggered.connect(self.enerpytypeBE)
        self.actionFriddle.triggered.connect(self.enerpytypeF)
        self.actionClustering_by_KMeans.triggered.connect(self.KNcluster)
        self.actionSort_by_similarity.triggered.connect(self.SimilaritySort)
        self.actionExit.triggered.connect(self.close)
        self.actionData_equipment.triggered.connect(self.dataEuipment)
        self.actionData_slimming.triggered.connect(self.dataSlimming)

    def enerpytypeBE(self) -> None:
        self.fitEnergy.start('BE')

    def enerpytypeF(self) -> None:
        self.fitEnergy.start('Friddle')

    def onmotion_event(self, event: Any) -> None:
        if self.press and None not in [self.ydata, self.xdata, event.xdata, event.ydata]:
            dx = event.xdata - self.xdata
            dy = event.ydata - self.ydata
            if self.control:
                self.F.plot_selrange(self.xdata, event.xdata)
                self.displace_result(range_fix=True)
            elif self.alt:
                self.pb.offset_move(dx, dy, True)
            else:
                self.F.motion(dx, dy)
            self.displace_result(range_fix=True)

    def on_release(self, event: Any) -> None:
        self.press = False
        self.xdata_r, self.ydata_r = event.xdata, event.ydata
        if None not in [self.xdata_r, self.xdata]:
            dx = event.xdata - self.xdata
            dy = event.ydata - self.ydata
            if self.control:
                self.pb.rebaseline_cal(self.xdata, event.xdata, allowRotate=self.allowrotate)
                self.F.plot_selrange(None, None)
                self.displace_result(range_fix=True)
            elif self.alt:
                self.pb.offset_move(dx, dy, False)

    def choose_zoom(self) -> None:
        self.zoomy_state = self.zoomy.isChecked()
        self.zoomx_state = self.zoomx.isChecked()
        self.zoomfix_state = self.zoomfix.isChecked()

    def on_press(self, event: Any) -> None:
        self.press = True
        if event.xdata is None or event.ydata is None:
            return None
        self.xdata = event.xdata
        self.ydata = event.ydata
        self.pb.coor_data = (self.xdata, self.ydata)
        self.pb.pk_indexchange(n=None, coor=(self.xdata, self.ydata))
        self.displace_result(range_fix=True)

    def scroll_event(self, event: Any) -> None:
        if self.xdata is not None and self.ydata is not None:
            event.xdata, event.ydata = self.xdata, self.ydata
        self.F.zoom_func(event, zoomx_state=self.zoomx_state, zoomy_state=self.zoomy_state)
        self.displace_result(range_fix=True)

    def openfile(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(self, "Load force curve", '*.txt;;*.jpk-force;;*.jpk-force-map;;*.spm')
        self.fname = fname
        if fname != '':
            self.pb.creattask(fname)

    def openfile_DataYee(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(self, "Open DataYee Force", '*.DataYee-force')
        self.fname = fname
        if fname != '':
            self.pb.creattask(fname)
            self.F.clean_overlay()
            self.displace_result()

    def opendir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, 'Load batch of force curve', '*.*')
        self.filedir = path
        if path != '':
            self.pb.creattask(path)

    def savefile(self) -> None:
        self.svfname = self.pb.zpo.fname
        if self.svfname == 'test.DataYee-force':
            self.svfname, _ = QFileDialog.getSaveFileName(self, 'Save DataYee Force', '*.DataYee-force')
        self.pb.savechange(self.svfname, saveas=True)

    def saveasfile(self) -> None:
        self.svfname = self.pb.zpo.fname
        svfname, _ = QFileDialog.getSaveFileName(self, 'Save DataYee Force', '*.DataYee-force')
        if svfname == '':
            QMessageBox.information(self, "Error", "Empty Path!")
        else:
            self.svfname = svfname
            self.pb.savechange(self.svfname, saveas=True)

    def aboutprogramm(self) -> None:
        QMessageBox.information(self, 'DataYee', 'Programm Version:0.1', QMessageBox.Ok | QMessageBox.Close, QMessageBox.Close)

    def displace_result(self, range_fix: bool = False) -> None:
        if range_fix:
            self.F.range_fix = True
        else:
            self.F.range_fix = False
        self.gridlayout.removeWidget(self.F.canvas)
        self.pb.plot(self.F)
        self.pb.drawlabel(self.label, self.lclplabel)
        self.F.canvas.draw()
        self.gridlayout.addWidget(self.F.canvas)

    def indexplus(self) -> None:
        self.pb.fc_indexchange(1)
        self.resetslide()
        self.spinBox.setValue(self.pb.forcecurve_index)
        self.displace_result(range_fix=self.zoomfix_state)

    def indexreduct(self) -> None:
        self.pb.fc_indexchange(-1)
        self.resetslide()
        self.spinBox.setValue(self.pb.forcecurve_index)
        self.displace_result(range_fix=self.zoomfix_state)

    def peakindexplus(self) -> None:
        self.pb.pk_indexchange(1)
        self.resetslide()
        self.displace_result(range_fix=self.zoomfix_state)

    def peakvalueplus(self) -> None:
        self.pb.pv_change(self.siglestep)
        self.displace_result(range_fix=self.zoomfix_state)

    def peakvalueminus(self) -> None:
        self.pb.pv_change(self.siglestep * -1)
        self.displace_result(range_fix=self.zoomfix_state)

    def peakindexretact(self) -> None:
        self.pb.pk_indexchange(-1)
        self.resetslide()
        self.displace_result(range_fix=self.zoomfix_state)

    def peakdelete(self) -> None:
        self.pb.pk_delete()
        self.resetslide()
        self.displace_result(range_fix=self.zoomfix_state)

    def forcedelete(self) -> None:
        self.pb.fc_delete()
        self.indexplus()
        self.resetslide()
        self.displace_result(range_fix=self.zoomfix_state)

    def reset_delete(self) -> None:
        self.pb.reset()
        self.displace_result(range_fix=self.zoomfix_state)

    def keyPressEvent(self, e: Any) -> None:
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
        elif e.key() == Qt.Key_Control:
            self.control = True
        elif e.key() == Qt.Key_Alt:
            self.alt = True
        elif Qt.Key_A <= e.key() <= Qt.Key_Z:
            self.pb.changeClass(chr(e.key()))
            self.indexplus()
            self.displace_result(range_fix=self.zoomfix_state)
        elif e.key() == Qt.Key_1:
            self.CurveKeep()
        elif e.key() == Qt.Key_2:
            self.CurveDiscard()

    def keyReleaseEvent(self, e: Any) -> None:
        if e.key() == Qt.Key_Control:
            self.control = False
        elif e.key() == Qt.Key_Alt:
            self.alt = False

    def resetslidevalue(self) -> None:
        self.lcslide.setValue(0)
        self.lpslide.setValue(0)

    def changemark(self) -> None:
        mark = self.lineEdit.text()
        if mark != '':
            self.pb.changemark(mark)
            self.displace_result(range_fix=self.zoomfix_state)

    def lcslidechange(self, value: int) -> None:
        self.lc_value = self.lcdoubleSpinBox.value()
        self.lp_value = self.lpdoubleSpinBox.value()
        self.pb.lc_change(value, self.lc_value)
        self.displace_result(range_fix=self.zoomfix_state)

    def lpslidechange(self, value: int) -> None:
        self.lc_value = self.lcdoubleSpinBox.value()
        self.lp_value = self.lpdoubleSpinBox.value()
        self.pb.lp_change(value, self.lp_value)
        self.displace_result(range_fix=self.zoomfix_state)

    def kslidechange(self, value: int) -> None:
        self.k_value = self.kSpinBox.value()
        self.pb.k_change(value, self.k_value)
        self.displace_result(range_fix=self.zoomfix_state)

    def resetslide(self) -> None:
        self.lcslide.setValue(0)
        self.lpslide.setValue(0)
        self.kSlider.setValue(0)

    def plot_contourhist(self) -> None:
        self.img = self.pb.plot_contourhist()
        self.showimage_win.show_img(self.img)

    def plot_contourscatter(self) -> None:
        self.img = self.pb.plot_contourscatter()
        self.showimage_win.show_img(self.img)

    def adhesionmap(self) -> None:
        self.img = self.pb.adhesionmap()
        self.showimage_win.show_img(self.img)

    def adhesionhist(self) -> None:
        self.img = self.pb.adhesionhist()
        self.showimage_win.show_img(self.img)

    def spinbox_changevalue(self, value: Any) -> None:
        sender = self.sender()
        if sender == self.spinBox_2:
            self.pb.taskarg['peakN'][0] = value
        elif sender == self.spinBox_3:
            self.pb.taskarg['peakN'][1] = value
        if not self.pb.state:
            return None
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
            self.displace_result(range_fix=self.zoomfix_state)

    def comboBoxchange(self, value: str) -> None:
        if value == 'Fix lc':
            self.pb.fixlc_changelp = True
        else:
            self.pb.fixlc_changelp = False

    def rbclicked(self) -> None:
        sender = self.sender()
        if sender == self.bg:
            if self.bg.checkedId() == 0:
                self.tasktype = 'smfs'
            elif self.bg.checkedId() == 1:
                self.tasktype = 'cell_curve'

    def copypeak(self) -> None:
        if self.xdata is None:
            return None
        self.pb.copypeak(self.xdata, self.ydata)
        self.displace_result(range_fix=self.zoomfix_state)

    def statemodel(self) -> None:
        self.pb.taskarg['usemodel'] = self.usemodel_cb.isChecked()
        self.pb.taskarg['modelstrict'] = self.stickmodel.isChecked()
        if self.fastmode.isChecked():
            self.pb.taskarg['fastmode'] = 'series'
        else:
            self.pb.taskarg['fastmode'] = 'img'

    def baselineplus(self) -> None:
        self.pb.baseline_change(5e-12)
        self.displace_result(range_fix=self.zoomfix_state)

    def baselineminus(self) -> None:
        self.pb.baseline_change(-5e-12)
        self.displace_result(range_fix=self.zoomfix_state)

    def exportexcel(self) -> None:
        self.pb.export_prodata(self)

    def exporttxt(self) -> None:
        self.pb.exporttxt()

    def exportbatchtxt(self) -> None:
        self.pb.exportbatchtxt()

    def export_figure(self) -> None:
        self.pb.export_figure(self.F.figure)

    def SimilaritySort(self) -> None:
        self.pb.SimilaritySort(self.m_run)

    def KNcluster(self) -> None:
        self.pb.KNcluster(self.m_run)

    def run(self) -> None:
        if not self.pb.ready_run:
            return None
        progress = QProgressDialog(self)
        self.pb.tasktype = self.tasktype
        self.pb.execu_autostep(progress, self)
        if self.pb.state:
            self.displace_result()

    def dataEuipment(self) -> None:
        self.pb.Data_equip_slim('e', QProgressDialog(self), self)

    def dataSlimming(self) -> None:
        self.pb.Data_equip_slim('s', QProgressDialog(self), self)

    def CurveKeep(self) -> None:
        self.pb.keepcurve()
        self.displace_result(range_fix=self.zoomfix_state)

    def CurveDiscard(self) -> None:
        self.pb.discardcurve()
        self.displace_result(range_fix=self.zoomfix_state)
