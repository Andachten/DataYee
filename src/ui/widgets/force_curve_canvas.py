from typing import Optional, Dict, List, Any, Tuple
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

COLOR_LSTS = ['#f76707'] * 9


def getfitcurve(wlcarg: List[Tuple[np.ndarray, ...]], peakindex: List[int], data_x: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Calculate WLC fit curves for given peak indices."""
    arg_lst = []
    for i, arg in enumerate(wlcarg):
        x_ = np.linspace(0, data_x[peakindex[i]] + 10)
        y_ = _lcfunc(x_, *arg)
        x_ = x_[:y_.argmax()]
        y_ = y_[:y_.argmax()]
        arg_lst.append((x_, y_))
    return arg_lst


def _lcfunc(x: np.ndarray, lc: float, lp: float, k: float, offset: float) -> np.ndarray:
    """WLC model function."""
    return k * (0.25 * (1 - x / lc + lp / x) ** -2 - 0.25 + x / lc - 5 * lp / (4 * x)) + offset


class ForceCurveCanvas(FigureCanvas):
    """Canvas widget for displaying force curves with WLC fits and peaks."""

    def __init__(self, parent: Optional[Any] = None) -> None:
        self.fig = Figure(dpi=100)
        self.ax = self.fig.add_subplot()
        self.ax.plot([-1e4, 1e4], [0, 0], lw=1.5, c='#ff8787')
        self.ax.plot([0, 0], [-50, 50], 'r-', lw=1)
        plt.subplots_adjust(left=0, bottom=0, right=1, top=0.5, hspace=0.1, wspace=0.1)
        self.index = 0
        self.content: Dict[str, List[Any]] = {
            'curve': [],
            'peak': [],
            'bottom': [],
            'mark': [],
            'fitcurve': [],
            'k': [],
            'selrange': [],
            'class': []
        }
        self.range_fix = False
        super().__init__(self.fig)
        self.overlay_dic: Dict[int, Any] = {}
        self.overlaymode = False
        self.data_x: Optional[np.ndarray] = None
        self.data_y: Optional[np.ndarray] = None

    def zoom_func(self, event: Any, base_scale: float = 1.1, zoomx_state: bool = True, zoomy_state: bool = True) -> None:
        if not zoomx_state and not zoomy_state:
            return None
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        cur_xrange = (cur_xlim[1] - cur_xlim[0]) * 0.5
        cur_yrange = (cur_ylim[1] - cur_ylim[0]) * 0.5
        xdata = event.xdata
        ydata = event.ydata
        if event.button == 'up':
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            scale_factor = base_scale
        else:
            scale_factor = 1
        if zoomx_state:
            self.ax.set_xlim([xdata - cur_xrange * scale_factor, xdata + cur_xrange * scale_factor])
        if zoomy_state:
            self.ax.set_ylim([ydata - cur_yrange * scale_factor, ydata + cur_yrange * scale_factor])

    def plot_selrange(self, datax1: Optional[float], datax2: Optional[float]) -> None:
        if self.fc.data['datamsg'][0] == '':
            return None
        if datax1 is None or datax2 is None:
            for line in self.content['selrange']:
                try:
                    line[0].remove()
                except Exception:
                    continue
            return None
        if datax1 > datax2:
            datax1, datax2 = datax2, datax1
        for line in self.content['selrange']:
            try:
                line[0].remove()
            except Exception:
                continue
        cur_ylim = self.ax.get_ylim()
        self.content['selrange'].append(self.ax.plot([datax1, datax1], cur_ylim, c='#9fa8da', lw=1))
        self.content['selrange'].append(self.ax.plot([datax2, datax2], cur_ylim, c='#9fa8da', lw=1))

    def overlay(self, curve_index: int) -> None:
        if 'overlay' not in self.fc.data.keys():
            self.fc.data['overlay'] = self.overlaymode
        index = curve_index
        if self.fc.data['overlay']:
            if index not in self.overlay_dic.keys():
                pass
            else:
                self.overlay_dic[index][0].remove()
                del self.overlay_dic[index]
            self.overlay_dic[index] = self.ax.plot(self.data_x[::10], self.data_y[::10], 'k', lw=1.5, alpha=0.1, markevery=10)
        else:
            if index in self.overlay_dic.keys():
                self.overlay_dic[index][0].remove()
                del self.overlay_dic[index]

    def clean_overlay(self) -> None:
        for i, v in self.overlay_dic.items():
            v[0].remove()
        self.overlay_dic = {}

    def motion(self, dx: float, dy: float) -> None:
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        x = (cur_xlim[1] + cur_xlim[0]) * 0.5 - dx
        y = (cur_ylim[1] + cur_ylim[0]) * 0.5 - dy
        cur_xrange = (cur_xlim[1] - cur_xlim[0]) * 0.5
        cur_yrange = (cur_ylim[1] - cur_ylim[0]) * 0.5
        self.ax.set_ylim([y - cur_yrange, y + cur_yrange])
        self.ax.set_xlim([x - cur_xrange, x + cur_xrange])

    def setlim(self, xlim: Tuple[float, float], ylim: Tuple[float, float]) -> None:
        if self.range_fix:
            return None
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

    def plotcurve(self) -> None:
        for line in self.content['curve']:
            line[0].remove()
        self.content['curve'] = []
        if not self.fc.data['artificial_judge']:
            self.content['curve'].append(self.ax.plot(self.data_x, self.data_y, 'b', lw=1.5))
        else:
            self.content['curve'].append(self.ax.plot(self.data_x, self.data_y, c='#495057', lw=1.5))

    def plotfitcurve(self) -> None:
        for line in self.content['fitcurve']:
            line[0].remove()
        self.content['fitcurve'] = []
        if len(self.fc.data['peakindex']) <= 0:
            return None
        data_x = self.fc.get_prodata()['retract']['measuredHeight'][:, 0] * 1e9
        fit_lst = getfitcurve(self.fc.data['wlcarg'], self.fc.data['peakindex'], data_x)
        color_lst = (len(self.fc.data['wlcarg']) // len(COLOR_LSTS) + 1) * COLOR_LSTS
        for i, xy_ in enumerate(fit_lst):
            x_, y_ = xy_
            self.content['fitcurve'].append(self.ax.plot(x_, y_, '-.', c=color_lst[i], lw=1.5))

    def plotpeak(self) -> None:
        for line in self.content['peak']:
            line[0].remove()
        self.content['peak'] = []
        peak_index = self.fc.data['peakindex']
        if len(peak_index) <= 0:
            return None
        self.content['peak'].append(
            (self.ax.plot(self.data_x[peak_index], self.data_y[peak_index], 'yo', markersize=8)))
        self.content['peak'].append(
            self.ax.plot(self.data_x[peak_index[self.index]], self.data_y[peak_index[self.index]], 'ro', markersize=8))

    def plotmark(self) -> None:
        for line in self.content['mark']:
            line.remove()
        self.content['mark'] = []
        font = {'family': 'serif', 'style': 'italic', 'weight': 'normal', 'color': 'red', 'size': 14}
        mark = self.fc.data['mark']
        if len(mark) <= 0:
            return None
        peak_index = self.fc.data['peakindex']
        for i in range(len(mark)):
            if mark[i] == 'none':
                font['color'] = 'red'
            else:
                font['color'] = 'blue'
            if i % 3 == 0:
                self.content['mark'].append(
                    self.ax.text(self.data_x[peak_index[i]] - 3, -70, f'{i}.{mark[i]}', font, horizontalalignment='left'))
            elif i % 3 == 1:
                self.content['mark'].append(
                    self.ax.text(self.data_x[peak_index[i]] - 3, -50, f'{i}.{mark[i]}', font, horizontalalignment='left'))
            elif i % 3 == 2:
                self.content['mark'].append(
                    self.ax.text(self.data_x[peak_index[i]] - 3, -30, f'{i}.{mark[i]}', font, horizontalalignment='left'))

    def plotk(self) -> None:
        for line in self.content['k']:
            line[0].remove()
        self.content['k'] = []
        peak_index = self.fc.data['peakindex']
        if len(peak_index) == 0:
            return None
        k_lst = self.fc.data['k']
        xrange = (self.data_x[peak_index[-1]] - self.data_x[0]) * 0.04
        yrange = (self.data_y.max() - self.data_y.min()) * 0.08
        for i, p_i in enumerate(peak_index):
            x, y = self.data_x[p_i], self.data_y[p_i]
            b = y - k_lst[i] * x
            x_ = np.linspace(x - xrange, x + xrange)
            y_ = k_lst[i] * x_ + b
            xyrange_index = np.where((y_ < y + yrange) & (y_ > y - yrange))[0]
            x_ = x_[xyrange_index]
            y_ = y_[xyrange_index]
            self.content['k'].append(self.ax.plot(x_, y_, 'b', lw=1))

    def plotclass(self) -> None:
        for line in self.content['class']:
            line.remove()
        self.content['class'] = []
        if 'class' not in self.fc.data.keys():
            c = 'N'
        else:
            c = self.fc.data['class']
        self.content['class'].append(
            self.ax.text(0.05, 0.9, c, fontsize=20, fontweight='bold', horizontalalignment='center',
                          verticalalignment='center', transform=self.ax.transAxes))

    def changeall(self) -> None:
        self.plotcurve()
        dx = np.abs(self.data_x.max()) - self.data_x.min()
        dy = np.abs(self.data_y.max()) - self.data_y.min()
        if len(self.fc.data['peakindex']) > 0:
            self.setlim((-10, self.data_x[self.fc.data['peakindex'][-1]] + 0.05 * dx),
                        (-90, self.data_y.max() + 0.1 * dy))
        else:
            self.setlim((-10, self.data_x.max() + 30), (-90, self.data_y.max() + 40))
        self.plotfitcurve()
        self.plotpeak()
        self.plotmark()
        self.plotk()
        self.plotclass()

    def plot(self, fc: Any, index: int, ljp: Any, tasktype: str = 'smfs', curve_index: int = 0) -> None:
        self.fc = fc
        self.fc.recover_force(ljp)
        self.index = index
        self.getdata()
        self.changeall()
        self.overlay(curve_index)
        if tasktype == 'cell_curve' and not self.range_fix:
            set_range = 0.1
            ylim_min = self.data_y[int(set_range * len(self.data_y)):].min() - 20
            self.setlim((self.data_x.min() - 20, self.data_x.max() + 0.1 * (self.data_x.max() - self.data_x.min())),
                        (ylim_min, self.data_y.max() + 10))
        plt.draw()

    def getdata(self) -> None:
        data = self.fc.get_prodata()['retract']
        self.data_y = data['vDeflection'][:, 0] * 1e12
        self.data_x = data['measuredHeight'][:, 0] * 1e9

    @property
    def figure(self) -> Figure:
        return self.fig


from src.loadjpk import forcecurve
ForceCurveCanvas.fc = forcecurve()
