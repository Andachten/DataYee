"""Force curve data model with type hints"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import numpy.typing as npt


@dataclass
class OffsetData:
    x: float = 0.0
    y: float = 0.0
    k: float = 0.0
    highspeed: float = 0.0
    k_alpha: float = 1.0
    rotate_index: Optional[int] = None


@dataclass
class FilterData:
    methods: str = "savgol"
    win_lens: int = 13
    poly: int = 2


@dataclass
class ForceCurveData:
    tasktype: str = ""
    rawdata: dict = field(default_factory=dict)
    path: str = ""
    springConstant: float = 0.01
    datamsg: tuple = ("", 0)
    offset: OffsetData = field(default_factory=OffsetData)
    filters: FilterData = field(default_factory=FilterData)
    mobilenet_judge: bool = True
    peaknum_judge: bool = True
    artificial_judge: bool = True
    peakindex: list = field(default_factory=list)
    bottomindex: list = field(default_factory=list)
    wlcarg: list = field(default_factory=list)
    dlc: list = field(default_factory=list)
    k: list = field(default_factory=list)
    mark: list = field(default_factory=list)
    arg: dict = field(default_factory=dict)
    xy_position: list = field(default_factory=lambda: [0, 0])
    compressed_data: dict = field(default_factory=dict)
    class_label: str = "N"
    overlay: bool = False


@dataclass
class WLCArm:
    lc: float
    lp: float


@dataclass
class TaskArguments:
    peakH: float = 30.0
    sens: float = 10.0
    peakN: tuple = (1, 6)
    xlim: float = 20.0
    lp: tuple = (0.34, 0.38)
    mark: dict = field(default_factory=lambda: {"GB1": (13, 23), "I27": (23, 36)})
    fitjudge: bool = False
    usemodel: bool = True
    xsens: float = 2.0
    highspeed: bool = False
    modelstrict: bool = False
    fastmode: str = "img"
