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


class ParaWindow(QDialog):
    """Parameter settings dialog window."""

    def __init__(self, pb: 'programbody', myWin: 'QMainWindow') -> None:
        super().__init__()
        from src.parameters import Ui_Dialog
        self.setupUi(self)
        self.pb = pb
        self.myWin = myWin
        self.myWin.allowrotate = False
        self.action_init()

    def setupUi(self, Dialog: QDialog) -> None:
        from src.parameters import Ui_Dialog
        super().setupUi(Dialog)
        Ui_Dialog.setupUi(self, Dialog)

    def action_init(self) -> None:
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
        self.delay.stateChanged.connect(self.cbchange)

    def spinbox_changevalue(self, value: float) -> None:
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
            self.pb.taskarg['lp'][0] = value

    def hispeedcorrect(self) -> None:
        if self.highspeed.isChecked():
            self.pb.taskarg['highspeed'] = True
        else:
            self.pb.taskarg['highspeed'] = False

    def cbchange(self) -> None:
        sender = self.sender()
        if sender == self.rotatestate:
            self.myWin.allowrotate = not self.myWin.allowrotate
        elif sender == self.delay:
            self.myWin.F.overlaymode = not self.myWin.F.overlaymode


class DLCRangeWindow(QDialog):
    """DLC range settings dialog window."""

    def __init__(self, myWin: 'QMainWindow') -> None:
        super().__init__()
        from src.dlcrange import Ui_dlc_range
        self.setupUi(self)
        self.myWin = myWin
        self.action_init()

    def setupUi(self, Dialog: QDialog) -> None:
        from src.dlcrange import Ui_dlc_range
        super().setupUi(Dialog)
        Ui_dlc_range.setupUi(self, Dialog)

    def action_init(self) -> None:
        self.pushButton.clicked.connect(self.table_update)

    def table_update(self) -> None:
        from src.datapro import is_number
        dic: Dict[str, tuple] = {}
        for r in range(1, 10):
            if (self.tableWidget.item(r, 0) is not None and
                self.tableWidget.item(r, 1) is not None and
                self.tableWidget.item(r, 2) is not None):
                if (is_number(self.tableWidget.item(r, 1).text()) and
                    is_number(self.tableWidget.item(r, 2).text()) and
                    float(self.tableWidget.item(r, 1).text()) <= float(self.tableWidget.item(r, 2).text()) and
                    float(self.tableWidget.item(r, 1).text()) > 0):
                    dic[self.tableWidget.item(r, 0).text()] = (
                        float(self.tableWidget.item(r, 1).text()),
                        float(self.tableWidget.item(r, 2).text())
                    )
                else:
                    QMessageBox.information(self, "Error", "Input error!")
                    return None
        d = np.diff(np.sort(np.array(list(dic.values())), axis=0).reshape(-1))
        if sum(np.where(d <= 0)[0]) != 0:
            QMessageBox.information(self, "Error", "Input error!")
            return None
        self.myWin.pb.taskarg['mark'] = dic
        self.close()


class ShowImageWindow(QDialog):
    """Image display dialog window."""

    def __init__(self) -> None:
        super().__init__()
        from src.showimage import Ui_image
        self.setupUi(self)

    def setupUi(self, Dialog: QDialog) -> None:
        from src.showimage import Ui_image
        super().setupUi(Dialog)
        Ui_image.setupUi(self, Dialog)

    def show_img(self, img: Any) -> None:
        if img is None:
            self.close()
            return None
        self.img = img
        scale = img.size[0] / 589
        self.frame = QImage(np.array(img), img.size[0], img.size[1], QImage.Format_RGB888)
        self.pix = QPixmap.fromImage(self.frame).scaledToWidth(int(img.size[0] / scale)).scaledToHeight(int(img.size[1] / scale))
        self.item = QGraphicsPixmapItem(self.pix)
        self.scene = QGraphicsScene()
        self.scene.addItem(self.item)
        self.graphicsView.setScene(self.scene)
        self.show()


class ScatterFigure(FigureCanvas):
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
        super().__init__(self.canvas.figure)

    def plotscatter(self, arr_dic: Dict[int, tuple], index: int) -> None:
        for s in self.s:
            s.remove()
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


class StatisticsWindow(QDialog):
    """Statistics dialog with scatter plot and histogram."""

    def __init__(self, myWin: 'QMainWindow') -> None:
        super().__init__()
        from src.scatter_histogramm import Ui_hist_scatter
        self.myWin = myWin
        self.setupUi(self)
        self.F = ScatterFigure()
        self.horizontalLayout_2.addWidget(self.F.canvas)
        self.force_index = 0
        self.arr_dic: Dict[int, tuple] = {}
        self.displace()
        self.action_init()

    def setupUi(self, Dialog: QDialog) -> None:
        from src.scatter_histogramm import Ui_hist_scatter
        super().setupUi(Dialog)
        Ui_hist_scatter.setupUi(self, Dialog)

    def action_init(self) -> None:
        self.pushButton.clicked.connect(self.delete)
        self.pushButton_4.clicked.connect(self.plot)
        self.pushButton_5.clicked.connect(self.save)
        self.pushButton_6.clicked.connect(self.openfile)

    def displace(self) -> None:
        self.F.clean()
        self.horizontalLayout_2.removeWidget(self.F.canvas)
        self.F.canvas.draw()
        self.horizontalLayout_2.addWidget(self.F.canvas)

    def get_data(self) -> None:
        if not self.myWin.pb.state and self.myWin.pb.tasktype != 'smfs':
            return None
        fc = self.myWin.pb.fc
        ljp = self.myWin.pb.ljp
        self.force_index = self.myWin.pb.forcecurve_index
        fc.recover_force(ljp)
        data = fc.get_prodata()['retract']
        data_y = data['vDeflection'].reshape(-1) * 1e12
        force_arr = data_y[fc.data['peakindex'][:-1]]
        print(force_arr)
        dlc_arr = fc.data['dlc']
        print(dlc_arr)
        self.arr_dic[self.force_index] = (dlc_arr, force_arr)
        fc.clean_force()
        self.fname = 'test.scatterplot'

    def plot(self) -> None:
        if not self.myWin.pb.state or self.myWin.pb.tasktype != 'smfs':
            return None
        self.get_data()
        self.F.plotscatter(self.arr_dic, self.force_index)
        self.F.plothisto(self.arr_dic)
        self.displace()

    def delete(self) -> None:
        self.force_index = self.myWin.pb.forcecurve_index
        if self.force_index in self.arr_dic.keys():
            del self.arr_dic[self.force_index]
        self.F.plotscatter(self.arr_dic, self.force_index)
        self.F.plothisto(self.arr_dic)
        self.displace()

    def save(self) -> None:
        import os
        import pickle
        if not self.myWin.pb.state or self.myWin.pb.tasktype != 'smfs':
            return None
        fname = self.myWin.pb.zpo.fname
        todir = os.path.dirname(fname)
        basename = os.path.basename(fname)
        rawname = os.path.splitext(basename)[0]
        fname = os.path.join(todir, f"{rawname}.scatterplot")
        with open(fname, 'wb') as f:
            data = dict(arr_dic=self.arr_dic)
            pickle.dump(data, f)

    def openfile(self) -> None:
        import os
        import pickle
        if not self.myWin.pb.state or self.myWin.pb.tasktype != 'smfs':
            return None
        fname = self.myWin.pb.zpo.fname
        todir = os.path.dirname(fname)
        basename = os.path.basename(fname)
        rawname = os.path.splitext(basename)[0]
        fname = os.path.join(todir, f"{rawname}.scatterplot")
        if not os.path.isfile(fname):
            fname, _ = QFileDialog.getOpenFileName(self, "Open Scatter Plot", '*.scatterplot')
        if os.path.isfile(fname):
            with open(fname, 'rb') as f:
                data = pickle.load(f)
                self.arr_dic = data['arr_dic']
            self.F.plotscatter(self.arr_dic, self.force_index)
            self.F.plothisto(self.arr_dic)
            self.displace()


class ScriptWindow(QDialog):
    """Script management dialog window."""

    def __init__(self, myWin: 'QMainWindow') -> None:
        super().__init__()
        from src.script import Ui_Script
        self.myWin = myWin
        self.setupUi(self)
        self.script_path = r'./scripts'
        self.get_script()
        self.renew_list2()
        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.listWidget_2.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.add_lst: list = []
        self.action_init()

    def setupUi(self, Dialog: QDialog) -> None:
        from src.script import Ui_Script
        super().setupUi(Dialog)
        Ui_Script.setupUi(self, Dialog)

    def action_init(self) -> None:
        self.pushButton.clicked.connect(self.add)
        self.pushButton_2.clicked.connect(self.delete)
        self.pushButton_3.clicked.connect(self.get_selectitem)
        self.pushButton_4.clicked.connect(self.quickstart)
        self.pushButton_5.clicked.connect(self.up)
        self.pushButton_6.clicked.connect(self.down)
        self.pushButton_7.clicked.connect(self.renew)
        self.pushButton_8.clicked.connect(self.get_path)

    def delete(self) -> None:
        self.get_selectitem()
        print(self.select_dic['add'])
        print(self.add_lst)
        for i in self.select_dic['add']:
            self.listWidget.removeItemWidget(self.listWidget.takeItem(self.listWidget.row(i)))
            self.add_lst.remove(i.text())

    def add(self) -> None:
        self.get_selectitem()
        for i in self.select_dic['script']:
            self.add_lst.append(i.text())
        self.renew_list1()

    def up(self) -> None:
        self.move(-1)

    def down(self) -> None:
        self.move(+1)

    def move(self, n: int) -> None:
        self.get_selectitem()
        for i, v in enumerate(self.select_dic['add']):
            index = self.listWidget.row(v)
            try:
                self.add_lst[index], self.add_lst[index + n] = self.add_lst[index + n], self.add_lst[index]
            except Exception:
                pass
            break
        self.renew_list1()

    def get_path(self) -> None:
        path = QFileDialog.getExistingDirectory(self, 'Load batch of force curve', '*.*')
        if path != '':
            self.script_path = path

    def get_selectitem(self) -> None:
        self.select_dic: Dict[str, list] = {}
        dic = {'add': self.listWidget, 'script': self.listWidget_2}
        for i in ['add', 'script']:
            self.select_dic[i] = []
            items = dic[i].selectedItems()
            for item in items:
                self.select_dic[i].append(item)

    def renew(self) -> None:
        self.listWidget_2.clear()
        self.get_script()
        self.renew_list2()

    def renew_list1(self) -> None:
        self.listWidget.clear()
        for i in self.add_lst:
            self.listWidget.addItem(i)

    def renew_list2(self) -> None:
        for fname in self.f_lst:
            self.listWidget_2.addItem(fname)

    def get_script(self) -> None:
        import os
        self.f_lst: list = []
        for a, b, c in os.walk(self.script_path):
            for fname in c:
                if fname.endswith('.py'):
                    self.f_lst.append(fname)

    def quickstart(self) -> None:
        import os
        import sys
        from importlib import reload
        zpo, ljp, fc = self.myWin.pb.zpo, self.myWin.pb.ljp, self.myWin.pb.fc
        index_lst = range(len(zpo))
        for i, v in enumerate(self.add_lst):
            print(v)
            name = os.path.splitext(v)[0]
            print(name)
            exec(f"from scripts.{name} import {name}")
            reload(sys.modules['scripts'])
            reload(sys.modules[f'scripts.{name}'])
            exec(f"from scripts.{name} import {name}")
            exec(f"{name}_{i} = {name}(zpo, ljp, fc)")
        for index in index_lst:
            for i, v in enumerate(self.add_lst):
                name = os.path.splitext(v)[0]
                try:
                    exec(f"{name}_{i}.run({index})")
                except Exception as err:
                    print(err)
        for i, v in enumerate(self.add_lst):
            name = os.path.splitext(v)[0]
            try:
                exec(f"{name}_{i}.end()")
            except Exception as err:
                print(err)
        print('finish')
