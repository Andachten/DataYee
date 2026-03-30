from typing import Any, Optional, Dict, TYPE_CHECKING
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QDialog, QMessageBox, QGraphicsScene, QGraphicsPixmapItem,
                             QApplication, QTableWidgetItem, QGridLayout, QFileDialog,
                             QAbstractItemView)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib as mpl
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from src.main import programbody
    from PyQt5.QtWidgets import QMainWindow


class TableHelper:
    """Helper class for table widget operations (copy, paste, cut)."""

    def __init__(self, table: Any) -> None:
        self.table = table

    def del_tb_text(self) -> None:
        try:
            selected_ranges = self.table.tableWidget.selectedRanges()[0]
            for row in range(selected_ranges.topRow(), selected_ranges.bottomRow() + 1):
                for col in range(selected_ranges.leftColumn(), selected_ranges.rightColumn() + 1):
                    newItem = QTableWidgetItem()
                    self.table.tableWidget.setItem(row, col, newItem)
        except Exception as e:
            print(e)

    def paste_tb_text(self) -> None:
        try:
            text = QApplication.clipboard().text()
            lst = text.split('\n')[:-1]
            lst1 = []
            for row in lst:
                lst1.append(row.split('\t'))
            selected_ranges = self.table.tableWidget.selectedRanges()[0]
            for r_i, row in enumerate(range(selected_ranges.topRow(), selected_ranges.topRow() + len(lst))):
                for c_i, col in enumerate(range(selected_ranges.leftColumn(), selected_ranges.leftColumn() + len(lst1[0]))):
                    newItem = QTableWidgetItem(lst1[r_i][c_i])
                    self.table.tableWidget.setItem(row, col, newItem)
        except Exception as e:
            print(e)

    def selected_tb_text(self) -> Optional[str]:
        try:
            text_str = ''
            selected_ranges = self.table.tableWidget.selectedRanges()[0]
            for row in range(selected_ranges.topRow(), selected_ranges.bottomRow() + 1):
                row_str = ""
                for col in range(selected_ranges.leftColumn(), selected_ranges.rightColumn() + 1):
                    item = self.table.tableWidget.item(row, col)
                    if item is None:
                        row_str += ' ' + '\t'
                    else:
                        row_str += item.text() + '\t'
                text_str += row_str + '\n'
            clipboard = QApplication.clipboard()
            clipboard.setText(text_str)
            return text_str
        except Exception as e:
            print(e)
            return None

    def copy(self) -> None:
        text = self.selected_tb_text()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

    def cut(self) -> None:
        self.copy()
        self.del_tb_text()

    def paste(self) -> None:
        self.paste_tb_text()


class ParaWindow:
    """Parameter settings dialog window."""

    def __init__(self, pb: 'programbody', myWin: 'QMainWindow') -> None:
        from src.parameters import Ui_Dialog
        self._dialog = QDialog()
        self._ui = Ui_Dialog()
        self._ui.setupUi(self._dialog)
        self._dialog.pb = pb
        self._dialog.myWin = myWin
        self._dialog.myWin.allowrotate = False
        self._dialog.sens = self._ui.sens
        self._dialog.xlimit = self._ui.xlimit
        self._dialog.xsens = self._ui.xsens
        self._dialog.peakH = self._ui.peakH
        self._dialog.highspeed = self._ui.highspeed
        self._dialog.spinBox = self._ui.spinBox
        self._dialog.lp_min = self._ui.lp_min
        self._dialog.lp_max = self._ui.lp_max
        self._dialog.rotatestate = self._ui.rotatestate
        self._dialog.delay = self._ui.delay
        self._setup_actions()

    def _setup_actions(self) -> None:
        self._dialog.sens.valueChanged.connect(self._spinbox_changevalue)
        self._dialog.xlimit.valueChanged.connect(self._spinbox_changevalue)
        self._dialog.xsens.valueChanged.connect(self._spinbox_changevalue)
        self._dialog.peakH.valueChanged.connect(self._spinbox_changevalue)
        self._dialog.highspeed.toggled.connect(self._hispeedcorrect)
        self._dialog.spinBox.valueChanged.connect(self._spinbox_changevalue)
        self._dialog.lp_min.valueChanged.connect(self._spinbox_changevalue)
        self._dialog.lp_max.valueChanged.connect(self._spinbox_changevalue)
        self._dialog.rotatestate.setChecked(False)
        self._dialog.rotatestate.stateChanged.connect(self._cbchange)
        self._dialog.delay.stateChanged.connect(self._cbchange)

    def _spinbox_changevalue(self, value: float) -> None:
        sender = self.sender()
        if sender == self._dialog.sens:
            self._dialog.pb.taskarg['sens'] = value
        elif sender == self._dialog.xlimit:
            self._dialog.pb.taskarg['xlim'] = value
        elif sender == self._dialog.xsens:
            self._dialog.pb.taskarg['xsens'] = value
        elif sender == self._dialog.peakH:
            self._dialog.pb.taskarg['peakH'] = value
        elif sender == self._dialog.spinBox:
            self._dialog.myWin.siglestep = value
        elif sender == self._dialog.lp_max:
            self._dialog.pb.taskarg['lp'][1] = value
        elif sender == self._dialog.lp_min:
            self._dialog.pb.taskarg['lp'][0] = value

    def _hispeedcorrect(self) -> None:
        if self._dialog.highspeed.isChecked():
            self._dialog.pb.taskarg['highspeed'] = True
        else:
            self._dialog.pb.taskarg['highspeed'] = False

    def _cbchange(self) -> None:
        sender = self.sender()
        if sender == self._dialog.rotatestate:
            self._dialog.myWin.allowrotate = not self._dialog.myWin.allowrotate
        elif sender == self._dialog.delay:
            self._dialog.myWin.F.overlaymode = not self._dialog.myWin.F.overlaymode

    def show(self) -> None:
        self._dialog.show()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._dialog, name)


class DLCRangeWindow:
    """DLC range settings dialog window."""

    def __init__(self, myWin: 'QMainWindow') -> None:
        from src.dlcrange import Ui_dlc_range
        self._dialog = QDialog()
        self._ui = Ui_dlc_range()
        self._ui.setupUi(self._dialog)
        self._dialog.myWin = myWin
        self._dialog.tableWidget = self._ui.tableWidget
        self._dialog.pushButton = self._ui.pushButton
        self._dialog.pushButton.clicked.connect(self._table_update)

    def _table_update(self) -> None:
        from src.datapro import is_number
        dic: Dict[str, tuple] = {}
        for r in range(1, 10):
            if (self._dialog.tableWidget.item(r, 0) is not None and
                self._dialog.tableWidget.item(r, 1) is not None and
                self._dialog.tableWidget.item(r, 2) is not None):
                if (is_number(self._dialog.tableWidget.item(r, 1).text()) and
                    is_number(self._dialog.tableWidget.item(r, 2).text()) and
                    float(self._dialog.tableWidget.item(r, 1).text()) <= float(self._dialog.tableWidget.item(r, 2).text()) and
                    float(self._dialog.tableWidget.item(r, 1).text()) > 0):
                    dic[self._dialog.tableWidget.item(r, 0).text()] = (
                        float(self._dialog.tableWidget.item(r, 1).text()),
                        float(self._dialog.tableWidget.item(r, 2).text())
                    )
                else:
                    QMessageBox.information(self._dialog, "Error", "Input error!")
                    return None
        d = np.diff(np.sort(np.array(list(dic.values())), axis=0).reshape(-1))
        if sum(np.where(d <= 0)[0]) != 0:
            QMessageBox.information(self._dialog, "Error", "Input error!")
            return None
        self._dialog.myWin.pb.taskarg['mark'] = dic
        self._dialog.close()

    def show(self) -> None:
        self._dialog.show()


class ShowImageWindow:
    """Image display dialog window."""

    def __init__(self) -> None:
        from src.showimage import Ui_image
        self._dialog = QDialog()
        self._ui = Ui_image()
        self._ui.setupUi(self._dialog)
        self._dialog.graphicsView = self._ui.graphicsView

    def show_img(self, img: Any) -> None:
        if img is None:
            self._dialog.close()
            return None
        self._img = img
        scale = img.size[0] / 589
        self._frame = QImage(np.array(img), img.size[0], img.size[1], QImage.Format_RGB888)
        self._pix = QPixmap.fromImage(self._frame).scaledToWidth(int(img.size[0] / scale)).scaledToHeight(int(img.size[1] / scale))
        self._item = QGraphicsPixmapItem(self._pix)
        self._scene = QGraphicsScene()
        self._scene.addItem(self._item)
        self._dialog.graphicsView.setScene(self._scene)
        self._dialog.show()


class ScatterFigure:
    """Scatter plot figure canvas for statistics window."""

    def __init__(self) -> None:
        self.canvas = FigureCanvas(mpl.figure.Figure(dpi=100))
        self.ax = self.canvas.figure.add_subplot(4, 1, (2, 4))
        self.ax0 = self.canvas.figure.add_subplot(4, 1, (1, 1))
        plt.subplots_adjust(left=0.3, bottom=0.2, right=0.9, top=0.9, hspace=0, wspace=0)
        self.index = 0
        self.content: Dict[str, list] = {
            'curve': [], 'peak': [], 'bottom': [], 'mark': [],
            'fitcurve': [], 'k': [], 'selrange': []
        }
        self.range_fix = False
        self.s: list = []
        self.h: list = []

    def plotscatter(self, arr_dic: Dict[int, tuple], index: int) -> None:
        for sc in self.s:
            sc.remove()
        self.s = []
        x = [v[0] for i, v in arr_dic.items() if i != index]
        y = [v[1] for i, v in arr_dic.items() if i != index]
        if 0 not in [len(x), len(y)]:
            arr_x = np.hstack(x)
            arr_y = np.hstack(y)
            self.s.append(self.ax.scatter(arr_x, arr_y, c='k'))
        x = [v[0] for i, v in arr_dic.items() if i == index]
        y = [v[1] for i, v in arr_dic.items() if i == index]
        if 0 not in [len(x), len(y)]:
            arr_x = np.hstack(x)
            arr_y = np.hstack(y)
            self.s.append(self.ax.scatter(arr_x, arr_y, c='r'))

    def plothisto(self, arr_dic: Dict[int, tuple]) -> None:
        for h in self.h:
            h.remove()
        x = [v[0] for i, v in arr_dic.items()]
        if 0 not in [len(x)]:
            arr_x = np.hstack(x)
            self.s.append(self.ax0.hist(arr_x, bins=10)[-1])

    def clean(self) -> None:
        for l in self.ax.lines:
            l.remove()


class StatisticsWindow:
    """Statistics dialog with scatter plot and histogram."""

    def __init__(self, myWin: 'QMainWindow') -> None:
        from src.scatter_histogramm import Ui_hist_scatter
        self._dialog = QDialog()
        self._ui = Ui_hist_scatter()
        self._ui.setupUi(self._dialog)
        self._myWin = myWin
        self.F = ScatterFigure()
        self._ui.horizontalLayout_2.addWidget(self.F.canvas)
        self._dialog.force_index = 0
        self._dialog.arr_dic: Dict[int, tuple] = {}
        self._displace()
        self._dialog.pushButton = self._ui.pushButton
        self._dialog.pushButton_4 = self._ui.pushButton_4
        self._dialog.pushButton_5 = self._ui.pushButton_5
        self._dialog.pushButton_6 = self._ui.pushButton_6
        self._dialog.pushButton.clicked.connect(self._delete)
        self._dialog.pushButton_4.clicked.connect(self._plot)
        self._dialog.pushButton_5.clicked.connect(self._save)
        self._dialog.pushButton_6.clicked.connect(self._openfile)

    def _displace(self) -> None:
        self.F.clean()
        self.F.canvas.draw()

    def _get_data(self) -> None:
        if not self._myWin.pb.state and self._myWin.pb.tasktype != 'smfs':
            return None
        fc = self._myWin.pb.fc
        ljp = self._myWin.pb.ljp
        self._dialog.force_index = self._myWin.pb.forcecurve_index
        fc.recover_force(ljp)
        data = fc.get_prodata()['retract']
        data_y = data['vDeflection'].reshape(-1) * 1e12
        force_arr = data_y[fc.data['peakindex'][:-1]]
        print(force_arr)
        dlc_arr = fc.data['dlc']
        print(dlc_arr)
        self._dialog.arr_dic[self._dialog.force_index] = (dlc_arr, force_arr)
        fc.clean_force()
        self._dialog.fname = 'test.scatterplot'

    def _plot(self) -> None:
        if not self._myWin.pb.state or self._myWin.pb.tasktype != 'smfs':
            return None
        self._get_data()
        self.F.plotscatter(self._dialog.arr_dic, self._dialog.force_index)
        self.F.plothisto(self._dialog.arr_dic)
        self._displace()

    def _delete(self) -> None:
        self._dialog.force_index = self._myWin.pb.forcecurve_index
        if self._dialog.force_index in self._dialog.arr_dic.keys():
            del self._dialog.arr_dic[self._dialog.force_index]
        self.F.plotscatter(self._dialog.arr_dic, self._dialog.force_index)
        self.F.plothisto(self._dialog.arr_dic)
        self._displace()

    def _save(self) -> None:
        import os
        import pickle
        if not self._myWin.pb.state or self._myWin.pb.tasktype != 'smfs':
            return None
        fname = self._myWin.pb.zpo.fname
        todir = os.path.dirname(fname)
        basename = os.path.basename(fname)
        rawname = os.path.splitext(basename)[0]
        fname = os.path.join(todir, f"{rawname}.scatterplot")
        with open(fname, 'wb') as f:
            data = dict(arr_dic=self._dialog.arr_dic)
            pickle.dump(data, f)

    def _openfile(self) -> None:
        import os
        import pickle
        if not self._myWin.pb.state or self._myWin.pb.tasktype != 'smfs':
            return None
        fname = self._myWin.pb.zpo.fname
        todir = os.path.dirname(fname)
        basename = os.path.basename(fname)
        rawname = os.path.splitext(basename)[0]
        fname = os.path.join(todir, f"{rawname}.scatterplot")
        if not os.path.isfile(fname):
            fname, _ = QFileDialog.getOpenFileName(self._dialog, "Open Scatter Plot", '*.scatterplot')
        if os.path.isfile(fname):
            with open(fname, 'rb') as f:
                data = pickle.load(f)
                self._dialog.arr_dic = data['arr_dic']
            self.F.plotscatter(self._dialog.arr_dic, self._dialog.force_index)
            self.F.plothisto(self._dialog.arr_dic)
            self._displace()

    def show(self) -> None:
        self._dialog.show()


class ScriptWindow:
    """Script management dialog window."""

    def __init__(self, myWin: 'QMainWindow') -> None:
        from src.script import Ui_Script
        self._dialog = QDialog()
        self._ui = Ui_Script()
        self._ui.setupUi(self._dialog)
        self._myWin = myWin
        self._dialog.script_path = r'./scripts'
        self._ui.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._ui.listWidget_2.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._dialog.add_lst: list = []
        self._dialog.listWidget = self._ui.listWidget
        self._dialog.listWidget_2 = self._ui.listWidget_2
        self._dialog.pushButton = self._ui.pushButton
        self._dialog.pushButton_2 = self._ui.pushButton_2
        self._dialog.pushButton_3 = self._ui.pushButton_3
        self._dialog.pushButton_4 = self._ui.pushButton_4
        self._dialog.pushButton_5 = self._ui.pushButton_5
        self._dialog.pushButton_6 = self._ui.pushButton_6
        self._dialog.pushButton_7 = self._ui.pushButton_7
        self._dialog.pushButton_8 = self._ui.pushButton_8
        self._setup_actions()

    def _setup_actions(self) -> None:
        self._dialog.pushButton.clicked.connect(self._add)
        self._dialog.pushButton_2.clicked.connect(self._delete)
        self._dialog.pushButton_3.clicked.connect(self._get_selectitem)
        self._dialog.pushButton_4.clicked.connect(self._quickstart)
        self._dialog.pushButton_5.clicked.connect(self._up)
        self._dialog.pushButton_6.clicked.connect(self._down)
        self._dialog.pushButton_7.clicked.connect(self._renew)
        self._dialog.pushButton_8.clicked.connect(self._get_path)

    def _delete(self) -> None:
        self._get_selectitem()
        print(self._dialog.select_dic['add'])
        print(self._dialog.add_lst)
        for i in self._dialog.select_dic['add']:
            self._dialog.listWidget.removeItemWidget(self._dialog.listWidget.takeItem(self._dialog.listWidget.row(i)))
            self._dialog.add_lst.remove(i.text())

    def _add(self) -> None:
        self._get_selectitem()
        for i in self._dialog.select_dic['script']:
            self._dialog.add_lst.append(i.text())
        self._renew_list1()

    def _up(self) -> None:
        self._move(-1)

    def _down(self) -> None:
        self._move(+1)

    def _move(self, n: int) -> None:
        self._get_selectitem()
        for i, v in enumerate(self._dialog.select_dic['add']):
            index = self._dialog.listWidget.row(v)
            try:
                self._dialog.add_lst[index], self._dialog.add_lst[index + n] = self._dialog.add_lst[index + n], self._dialog.add_lst[index]
            except Exception:
                pass
            break
        self._renew_list1()

    def _get_path(self) -> None:
        path = QFileDialog.getExistingDirectory(self._dialog, 'Load batch of force curve', '*.*')
        if path != '':
            self._dialog.script_path = path

    def _get_selectitem(self) -> None:
        self._dialog.select_dic: Dict[str, list] = {}
        dic = {'add': self._dialog.listWidget, 'script': self._dialog.listWidget_2}
        for i in ['add', 'script']:
            self._dialog.select_dic[i] = []
            items = dic[i].selectedItems()
            for item in items:
                self._dialog.select_dic[i].append(item)

    def _renew(self) -> None:
        self._dialog.listWidget_2.clear()
        self._get_script()
        self._renew_list2()

    def _renew_list1(self) -> None:
        self._dialog.listWidget.clear()
        for i in self._dialog.add_lst:
            self._dialog.listWidget.addItem(i)

    def _renew_list2(self) -> None:
        for fname in self._dialog.f_lst:
            self._dialog.listWidget_2.addItem(fname)

    def _get_script(self) -> None:
        import os
        self._dialog.f_lst: list = []
        for a, b, c in os.walk(self._dialog.script_path):
            for fname in c:
                if fname.endswith('.py'):
                    self._dialog.f_lst.append(fname)

    def _quickstart(self) -> None:
        import os
        import sys
        from importlib import reload
        zpo, ljp, fc = self._myWin.pb.zpo, self._myWin.pb.ljp, self._myWin.pb.fc
        index_lst = range(len(zpo))
        for i, v in enumerate(self._dialog.add_lst):
            print(v)
            name = os.path.splitext(v)[0]
            print(name)
            exec(f"from scripts.{name} import {name}")
            reload(sys.modules['scripts'])
            reload(sys.modules[f'scripts.{name}'])
            exec(f"from scripts.{name} import {name}")
            exec(f"{name}_{i} = {name}(zpo, ljp, fc)")
        for index in index_lst:
            for i, v in enumerate(self._dialog.add_lst):
                name = os.path.splitext(v)[0]
                try:
                    exec(f"{name}_{i}.run({index})")
                except Exception as err:
                    print(err)
        for i, v in enumerate(self._dialog.add_lst):
            name = os.path.splitext(v)[0]
            try:
                exec(f"{name}_{i}.end()")
            except Exception as err:
                print(err)
        print('finish')

    def show(self) -> None:
        self._dialog.show()
