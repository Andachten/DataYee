"""File I/O module for loading force curve data from various formats.

Supports:
- JPK force files (.jpk-force, .jpk-force-map)
- Text files (.txt)
- DataYee archive files (.DataYee-force)
- SPM files (.spm)
"""

from __future__ import annotations

import os
import copy
import time
import numpy as np
import numpy.typing as npt
import pickle
import zipfile
from zipfile import ZipFile
from scipy.signal import savgol_filter
from typing import Optional, Iterator
import lzma

from src.jpkfile import JPKFile, JPKMap


def rotate(
    data_x: npt.NDArray[np.float64],
    data_y: npt.NDArray[np.float64],
    index: int | tuple,
    k: float,
) -> npt.NDArray[np.float64]:
    """Rotate data around a point.

    Args:
        data_x: X data array
        data_y: Y data array
        index: Rotation point (index or tuple of coordinates)
        k: Rotation coefficient

    Returns:
        Rotated y data
    """
    theta = np.arctan(k) * -1
    if isinstance(index, int):
        return (
            (data_x - data_x[index]) * np.sin(theta)
            + (data_y - data_y[index]) * np.cos(theta)
            + data_y[index]
        )
    elif isinstance(index, tuple):
        return (
            (data_x - index[0]) * np.sin(theta)
            + (data_y - index[1]) * np.cos(theta)
            + index[1]
        )
    return data_y


class forcecurve:
    """Container class for a single force curve."""

    def __init__(self) -> None:
        """Initialize force curve with default data structure."""
        self.data: dict = {
            "tasktype": "",
            "rawdata": {},
            "path": "",
            "springConstant": 0.01,
            "datamsg": ("", 0),
            "offset": {"x": 0, "y": 0, "k": 0, "highspeed": 0, "k_alpha": 1},
            "filters": {"methods": "savgol", "win_lens": 13, "poly": 2},
            "mobilenet_judge": True,
            "peaknum_judge": True,
            "artificial_judge": True,
            "peakindex": [],
            "bottomindex": [],
            "wlcarg": [],
            "dlc": [],
            "k": [],
            "mark": [],
            "arg": {},
            "xy-position": [0, 0],
            "compressed_data": {},
            "class": "N",
            "overlay": False,
        }
        self._datatype = [("measuredHeight", "<f4"), ("vDeflection", "<f4")]

    def get_prodata(
        self, smooth: bool = True, tip_correc: bool = True, s: Optional[int] = None
    ) -> dict:
        """Get processed force curve data.

        Args:
            smooth: Apply smoothing filter
            tip_correc: Apply tip correction
            s: Custom smoothing window length

        Returns:
            Processed data dictionary
        """
        data = copy.deepcopy(self.data["rawdata"])
        if "k_alpha" not in self.data["offset"].keys():
            self.data["offset"]["k_alpha"] = 1
        for k, v in data.items():
            data[k]["vDeflection"] *= self.data["offset"]["k_alpha"]
            data[k]["measuredHeight"] = data[k]["measuredHeight"] - float(
                self.data["offset"]["x"]
            )
            data[k]["vDeflection"] = data[k]["vDeflection"] - self.data["offset"]["y"]
            if smooth and k == "retract":
                if s is None:
                    data[k]["vDeflection"] = savgol_filter(
                        data[k]["vDeflection"][:, 0],
                        self.data["filters"]["win_lens"],
                        self.data["filters"]["poly"],
                    ).reshape(len(data[k]["vDeflection"]), 1)
                else:
                    data[k]["vDeflection"] = savgol_filter(
                        data[k]["vDeflection"][:, 0], s, 2
                    ).reshape(len(data[k]["vDeflection"]), 1)
            data[k]["vDeflection"] *= -1
            if tip_correc:
                data[k]["measuredHeight"] = (
                    data[k]["measuredHeight"]
                    - (data[k]["vDeflection"] - data[k]["vDeflection"].min())
                    / self.data["springConstant"]
                )
            if "k" in self.data["offset"].keys():
                if "rotate_index" in self.data["offset"].keys():
                    rotate_index = self.data["offset"]["rotate_index"]
                else:
                    rotate_index = -1
                rotate_x = data["retract"]["measuredHeight"][rotate_index]
                rotate_y = data["retract"]["vDeflection"][rotate_index]
                data[k]["vDeflection"] = rotate(
                    data[k]["measuredHeight"].reshape(-1),
                    data[k]["vDeflection"].reshape(-1),
                    (rotate_x, rotate_y),
                    self.data["offset"]["k"],
                ).reshape(-1, 1)

        return data

    def savedata2txt(self, savedir: str = "data.txt") -> None:
        """Save force curve data to text file.

        Args:
            savedir: Path to save file
        """
        data = self.get_prodata(tip_correc=False)
        data_re = data["retract"]
        f = data_re["vDeflection"].reshape(-1)
        h = data_re["measuredHeight"].reshape(-1)
        data2save = np.dstack((f, h))[0]
        now = int(time.time())
        timeArray = time.localtime(now)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        header = ""
        header += otherStyleTime
        header += "\n"
        header += "springConstant:" + str(self.data["springConstant"]) + "N/m"
        with open(savedir, "w") as f:
            np.savetxt(f, data2save, header=header, fmt="%.6e")

    def compress(self) -> None:
        """Compress raw data using LZMA."""
        self.data["compressed_data"] = {}
        for item, value in self.data["rawdata"].items():
            self.data["compressed_data"][item] = (
                lzma.compress(
                    value.astype(
                        [("measuredHeight", "<f4"), ("vDeflection", "<f4")]
                    ).tobytes()
                ),
                eval(str(value.dtype).replace("<f8", "<f4")),
            )

    def decompress(self) -> None:
        """Decompress raw data from LZMA."""
        for item, value in self.data["compressed_data"].items():
            self.data["rawdata"][item] = np.frombuffer(
                lzma.decompress(value[0]), value[1]
            ).reshape(-1, 1)

    def clean_force(self) -> None:
        """Clear raw data from memory."""
        self.data["rawdata"] = {}

    def recover_force(self, ljf: Optional[loadjpkfile] = None) -> bool:
        """Recover force curve data from compressed or file source.

        Args:
            ljf: File loader object

        Returns:
            True if recovery successful
        """
        if len(self.data["rawdata"]) != 0:
            return True
        self.data["rawdata"] = {}
        if (
            "compressed_data" not in self.data.keys()
            or self.data["compressed_data"] == {}
        ):
            if ljf is None:
                return False
            ljf.file_type_deter(*self.data["datamsg"])
            self.data["rawdata"] = ljf.data["rawdata"]
            self.compress()
        self.decompress()
        return True


class loadjpkfile:
    """Batch file loader for force curve files."""

    def __init__(self, filedir: str) -> None:
        """Initialize file loader.

        Args:
            filedir: Path to file or directory
        """
        self.filedir = filedir
        self.filelst: list[str] = []
        self.datalst: list[tuple[str, int]] = []
        self.get_filelst()
        self.get_datalst()
        self.startnum = -1
        self.current_readfile = "none"
        fc = forcecurve()
        self.data = fc.data
        self.data["path"] = self.filedir
        self.buffer: dict = {
            "txt": "none",
            "jpkmap": "none",
            "jpkforce": "nono",
            "datay": "none",
        }
        self.datatype = [("measuredHeight", "<f4"), ("vDeflection", "<f4")]

    def __len__(self) -> int:
        """Return number of force curves."""
        return len(self.datalst)

    def __iter__(self) -> Iterator:
        """Return iterator."""
        return self

    def __next__(self) -> dict:
        """Get next force curve."""
        self.startnum += 1
        if self.startnum < len(self):
            pass
        else:
            self.startnum = -1
            raise StopIteration
        self.data["datamsg"] = self.datalst[self.startnum]
        self.file_type_deter(*self.datalst[self.startnum])
        return copy.deepcopy(self.data)

    def __getitem__(self, index: int) -> dict:
        """Get force curve by index."""
        self.file_type_deter(*self.datalst[index])
        self.data["datamsg"] = self.datalst[index]
        return copy.deepcopy(self.data)

    def get_datalst(self) -> None:
        """Build list of all force curves in files."""
        for fname in self.filelst:
            if sum(True for i in [".txt", ".jpk-force", ".datay"] if fname.endswith(i)):
                self.datalst.append((fname, 0))
            elif sum(True for i in [".jpk-force-map"] if fname.endswith(i)):
                properties = ZipFile(fname).open("header.properties")
                while True:
                    line = properties.readline()
                    if b"force-scan-map.indexes.max" in line:
                        maxindex = int(line.rstrip().split(b"=")[-1])
                        for i in range(maxindex):
                            self.datalst.append((fname, i))
                        break

    def get_filelst(self, Travel: bool = True) -> None:
        """Build list of all files in directory.

        Args:
            Travel: Whether to recursively traverse subdirectories
        """
        if os.path.isfile(self.filedir):
            self.filelst.append(self.filedir)
        elif os.path.isdir(self.filedir):
            for a, _b, c in os.walk(self.filedir, topdown=True, onerror=None, followlinks=False):
                for filename in c:
                    if sum(
                        True
                        for i in [
                            ".txt",
                            ".jpk-force",
                            ".jpk-force-map",
                            ".datay",
                            ".spm",
                        ]
                        if os.path.join(a, filename).endswith(i)
                    ):
                        self.filelst.append(os.path.join(a, filename))
                if not Travel:
                    break

    def file_type_deter(self, filename: str, index: int) -> None:
        """Determine file type and extract data.

        Args:
            filename: Path to file
            index: Force curve index within file
        """
        self.change_buffer(filename)
        if filename.endswith(".txt"):
            self.extract_txt_data(filename, index)
        elif filename.endswith(".jpk-force"):
            self.extract_force_data(filename, index)
        elif filename.endswith(".jpk-force-map"):
            self.extract_map_data(filename, index)
        elif filename.endswith(".datay"):
            self.extract_datay_data(filename, index)
        elif filename.endswith(".spm"):
            self.extract_spm_data(filename, index)

    def change_buffer(self, filename: str) -> None:
        """Update file buffer for current file.

        Args:
            filename: Path to file
        """
        if self.current_readfile != filename:
            self.current_readfile = filename
            suffix = os.path.splitext(filename)[-1]
            if suffix == ".txt":
                self.buffer["txt"] = np.loadtxt(filename, comments="#")
            elif suffix == ".jpk-force":
                self.buffer["jpkforce"] = JPKFile(filename)
            elif suffix == ".jpk-force-map":
                self.buffer["jpkmap"] = JPKMap(filename)
            elif suffix == ".datay":
                with open(filename, "rb") as f:
                    self.buffer["datay"] = pickle.load(f)

    def extract_txt_data(self, filename: str, index: int) -> None:
        """Extract data from text file.

        Args:
            filename: Path to file
            index: Curve index
        """
        data = self.buffer["txt"]
        springConstant = 0.01
        with open(filename, "r") as f:
            text = f.readlines()
            for line in text:
                if "# springConstant" in line:
                    springConstant = float(line.split()[-1])
                    break
        self.data["springConstant"] = springConstant
        self.data["rawdata"]["extend"] = np.array(
            [[tuple(i)] for i in data[: np.argmin(data[:, 0])]],
            dtype=self.datatype,
        )
        self.data["rawdata"]["retract"] = np.array(
            [[tuple(i)] for i in data[np.argmin(data[:, 0]) :]],
            dtype=self.datatype,
        )

    def extract_force_data(self, filename: str, index: int) -> None:
        """Extract data from JPK force file.

        Args:
            filename: Path to file
            index: Curve index
        """
        jpk = self.buffer["jpkforce"]
        springConstant = 0
        for i in ["1", "2"]:
            try:
                springConstant = float(
                    jpk.shared_parameters["lcd-info"][i]["conversion-set"][
                        "conversion"
                    ]["force"]["scaling"]["multiplier"]
                )
                break
            except Exception:
                continue
        if springConstant == 0:
            return None
        self.data["springConstant"] = springConstant
        for i, segment in jpk.segments.items():
            self.data["rawdata"][segment.get_info("type")] = segment.get_array(
                ["measuredHeight", "vDeflection"]
            )[0]

    def extract_map_data(self, filename: str, index: int) -> None:
        """Extract data from JPK force map file.

        Args:
            filename: Path to file
            index: Pixel index
        """
        jpks = self.buffer["jpkmap"]
        jpk = jpks.get_single_pixel(index)
        position = jpks.flat_indices[index].parameters["force-scan-series"][
            "header"
        ]["position"]
        self.data["xy-position"][0] = float(position["x"])
        self.data["xy-position"][1] = float(position["y"])
        try:
            springConstant = float(
                jpk.shared_parameters["lcd-info"]["2"]["conversion-set"][
                    "conversion"
                ]["force"]["scaling"]["multiplier"]
            )
        except Exception:
            springConstant = float(
                jpk.shared_parameters["lcd-info"]["1"]["conversion-set"][
                    "conversion"
                ]["force"]["scaling"]["multiplier"]
            )
        self.data["springConstant"] = springConstant
        for i, segment in jpk.segments.items():
            self.data["rawdata"][segment.get_info("type")] = segment.get_array(
                ["measuredHeight", "vDeflection"]
            )[0]

    def extract_datay_data(self, filename: str, index: int) -> None:
        """Extract data from DataYee pickle file.

        Args:
            filename: Path to file
            index: Curve index
        """
        self.data["springConstant"] = self.buffer["datay"]["springConstant"]
        self.data["rawdata"] = self.buffer["datay"]["rawdata"]

    def extract_spm_data(self, fname: str, index: int) -> None:
        """Extract data from SPM file (currently not implemented).

        Args:
            fname: Path to file
            index: Curve index
        """
        pass


class loadjpkfile_(forcecurve):
    """Alternative file loader with forcecurve inheritance."""

    def __init__(self, filedir: str) -> None:
        """Initialize alternative file loader.

        Args:
            filedir: Path to file or directory
        """
        super().__init__()
        self.filedir = filedir
        self.filelst: list[str] = []
        self.datalst: list[tuple[str, int]] = []
        self.get_filenamelst()
        self.get_dataindex()
        self.startnum = -1
        self.data_structure = copy.deepcopy(self.data)

    def __len__(self) -> int:
        """Return number of force curves."""
        return len(self.datalst)

    def __iter__(self) -> Iterator:
        """Return iterator."""
        return self

    def __next__(self) -> dict:
        """Get next force curve."""
        self.startnum += 1
        if self.startnum < len(self.datalst):
            pass
        else:
            self.startnum = -1
            raise StopIteration
        self.data = copy.deepcopy(self.data_structure)
        self.file_type_deter(*self.datalst[self.startnum])
        self.data["datamsg"] = self.datalst[self.startnum]
        self.data["path"] = self.filedir
        return self.data

    def __getitem__(self, index: int) -> dict:
        """Get force curve by index."""
        self.data = copy.deepcopy(self.data_structure)
        self.file_type_deter(*self.datalst[index])
        self.data["datamsg"] = self.datalst[index]
        self.data["path"] = self.filedir
        return self.data

    def get_dataindex(self) -> None:
        """Build list of all force curves."""
        for fname in self.filelst:
            if sum(True for i in [".txt", ".jpk-force", ".datay"] if fname.endswith(i)):
                self.datalst.append((fname, 0))
            elif sum(True for i in [".jpk-force-map"] if fname.endswith(i)):
                properties = ZipFile(fname).open("header.properties")
                while True:
                    line = properties.readline()
                    if b"force-scan-map.indexes.max" in line:
                        maxindex = int(line.rstrip().split(b"=")[-1])
                        for i in range(maxindex):
                            self.datalst.append((fname, i))
                        break

    def get_filenamelst(self, Travel: bool = True) -> None:
        """Build list of all files.

        Args:
            Travel: Whether to recursively traverse
        """
        if os.path.isfile(self.filedir):
            self.filelst.append(self.filedir)
        elif os.path.isdir(self.filedir):
            for a, _b, c in os.walk(
                self.filedir, topdown=True, onerror=None, followlinks=False
            ):
                for filename in c:
                    if sum(
                        True
                        for i in [".txt", ".jpk-force", ".jpk-force-map", ".datay"]
                        if os.path.join(a, filename).endswith(i)
                    ):
                        self.filelst.append(os.path.join(a, filename))
                if not Travel:
                    break

    def file_type_deter(self, filename: str, index: int) -> None:
        """Determine file type and extract data."""
        if filename.endswith(".txt"):
            self.extract_txt_data(filename, index)
        elif filename.endswith(".jpk-force"):
            self.extract_force_data(filename, index)
        elif filename.endswith(".jpk-force-map"):
            self.extract_map_data(filename, index)
        elif filename.endswith(".datay"):
            self.extract_datay_data(filename, index)

    def extract_txt_data(self, filename: str, index: int) -> None:
        """Extract data from text file."""
        data = np.loadtxt(filename, comments="#")
        springConstant = 0.01
        with open(filename, "r") as f:
            text = f.readlines()
            for line in text:
                if "# springConstant" in line:
                    springConstant = float(line.split()[-1])
                    break
        self.data["springConstant"] = springConstant
        self.data["rawdata"]["extend"] = np.array(
            [[tuple(i)] for i in data[: np.argmin(data[:, 0])]],
            dtype=self.datatype,
        )
        self.data["rawdata"]["retract"] = np.array(
            [[tuple(i)] for i in data[np.argmin(data[:, 0]) :]],
            dtype=self.datatype,
        )

    def extract_force_data(self, filename: str, index: int) -> None:
        """Extract data from JPK force file."""
        try:
            jpk = JPKFile(filename)
        except Exception:
            return None
        try:
            springConstant = float(
                jpk.shared_parameters["lcd-info"]["2"]["conversion-set"][
                    "conversion"
                ]["force"]["scaling"]["multiplier"]
            )
        except Exception:
            return None
        self.data["springConstant"] = springConstant
        for i, segment in jpk.segments.items():
            self.data["rawdata"][segment.get_info("type")] = segment.get_array(
                ["measuredHeight", "vDeflection"]
            )[0]

    def extract_map_data(self, filename: str, index: int) -> None:
        """Extract data from JPK force map file."""
        try:
            jpks = JPKMap(filename)
        except Exception:
            return None
        jpk = jpks.get_single_pixel(index)
        position = jpks.flat_indices[index].parameters["force-scan-series"][
            "header"
        ]["position"]
        self.data["xy-position"][0] = float(position["x"])
        self.data["xy-position"][1] = float(position["y"])
        try:
            springConstant = float(
                jpk.shared_parameters["lcd-info"]["2"]["conversion-set"][
                    "conversion"
                ]["force"]["scaling"]["multiplier"]
            )
        except Exception:
            springConstant = float(
                jpk.shared_parameters["lcd-info"]["1"]["conversion-set"][
                    "conversion"
                ]["force"]["scaling"]["multiplier"]
            )
        self.data["springConstant"] = springConstant
        for i, segment in jpk.segments.items():
            self.data["rawdata"][segment.get_info("type")] = segment.get_array(
                ["measuredHeight", "vDeflection"]
            )[0]

    def extract_datay_data(self, filename: str, index: int) -> None:
        """Extract data from DataYee pickle file."""
        with open(filename, "rb") as f:
            pkl = pickle.load(f)
        self.data["springConstant"] = pkl["springConstant"]
        self.data["rawdata"] = pkl["rawdata"]

    def extract_all_map2datay(self, todir: str) -> None:
        """Export all force curves from map file to DataYee format.

        Args:
            todir: Output directory
        """
        dic = self.data_structure
        for filename in self.filelst:
            if filename.endswith(".jpk-force-map"):
                jpks = JPKMap(filename)
                for i, j in jpks.flat_indices.items():
                    jpk = jpks.get_single_pixel(i)
                    position = j.parameters["force-scan-series"]["header"][
                        "position"
                    ]
                    dic["xy-position"][0] = float(position["x"])
                    dic["xy-position"][1] = float(position["y"])
                    try:
                        springConstant = float(
                            jpk.shared_parameters["lcd-info"]["2"]["conversion-set"][
                                "conversion"
                            ]["force"]["scaling"]["multiplier"]
                        )
                    except Exception:
                        springConstant = float(
                            jpk.shared_parameters["lcd-info"]["1"]["conversion-set"][
                                "conversion"
                            ]["force"]["scaling"]["multiplier"]
                        )
                    dic["springConstant"] = springConstant
                    dic["datamsg"] = (filename, i)
                    for n, segment in jpk.segments.items():
                        dic["rawdata"][segment.get_info("type")] = segment.get_array(
                            ["measuredHeight", "vDeflection"]
                        )[0]
                    fname = "{}-{}.datay".format(
                        os.path.join(
                            todir, os.path.splitext(os.path.basename(filename))[0]
                        ),
                        i,
                    )
                    with open(fname, "wb") as f:
                        pickle.dump(dic, f)


class zipfileopera:
    """Archive manager for DataYee force archives (.DataYee-force)."""

    def __init__(self, fname: str = "test.DataYee-force") -> None:
        """Initialize archive manager.

        Args:
            fname: Path to archive file
        """
        self.fname = fname
        self.startnum = -1
        self.version = "version2"
        self.data: dict = {self.version: "", "data.pkl": {}}
        self.readfile()
        self.change: dict = {}
        self.delete: list = []

    def __len__(self) -> int:
        """Return number of force curves in archive."""
        return len(self.data["data.pkl"])

    def __getitem__(self, index: int) -> dict:
        """Get force curve by index."""
        index = list(self.data["data.pkl"].keys())[index]
        return self.data["data.pkl"][index]

    def readfile(self) -> None:
        """Read archive file."""
        if os.path.isfile(self.fname):
            with ZipFile(self.fname, "r", zipfile.ZIP_DEFLATED) as zips:
                if self.version in zips.namelist():
                    for fname in zips.namelist():
                        with zips.open(fname) as f:
                            self.data[fname] = pickle.load(f)
                else:
                    for fname in zips.namelist():
                        if os.path.splitext(fname)[-1] == ".pkl":
                            with zips.open(fname) as f:
                                fcdata = pickle.load(f)
                                self.data["data.pkl"][fcdata["datamsg"]] = fcdata

    def savefile(self) -> None:
        """Save archive file."""
        with ZipFile(self.fname, "w", zipfile.ZIP_DEFLATED) as zips:
            for k, v in self.data.items():
                zips.writestr(k, pickle.dumps(v))

    def get_sourcepath(self) -> str:
        """Get source file path from first entry."""
        return list(self.data["data.pkl"].values())[0]["path"]

    def addforce(self, fc: forcecurve) -> None:
        """Add force curve to archive.

        Args:
            fc: Force curve object
        """
        fc.clean_force()
        self.data["data.pkl"][fc.data["datamsg"]] = fc.data

    def changingforce(self, fc: forcecurve) -> None:
        """Mark force curve as changed.

        Args:
            fc: Force curve object
        """
        fc.clean_force()
        self.change[fc.data["datamsg"]] = copy.deepcopy(fc.data)

    def deletingforce(self, fc: forcecurve) -> None:
        """Mark force curve for deletion.

        Args:
            fc: Force curve object
        """
        self.delete.append(fc.data["datamsg"])

    def deletedforce(self) -> None:
        """Delete marked force curves from archive."""
        for d in self.delete:
            if d in self.data["data.pkl"].keys():
                del self.data["data.pkl"][d]
        self.delete = []
        self.savefile()

    def clean_force(self) -> None:
        """Clear all data from archive."""
        self.data["data.pkl"] = {}

    def changedforce(
        self, svfname: str = "123.DataYee-force", saveas: bool = False, save: bool = True
    ) -> None:
        """Apply changes and save archive.

        Args:
            svfname: Save file name
            saveas: Whether to save as new file
            save: Whether to save to disk
        """
        if saveas:
            self.fname = svfname
        for k, v in self.change.items():
            self.data["data.pkl"][k] = v
        self.change = {}
        if save:
            self.savefile()

    def delet_dataYee(self) -> None:
        """Delete archive file and clear data."""
        self.data = {self.version: "", "data.pkl": {}}
        if os.path.isfile(self.fname):
            os.remove(self.fname)

    def get_maxforce(
        self,
        ljp: loadjpkfile,
        filters: bool = True,
        filter_lst: list = ["peaknum_judge", "mobilenet_judge", "artificial_judge"],
    ) -> npt.NDArray[np.float64]:
        """Get maximum force values for all curves.

        Args:
            ljp: File loader
            filters: Whether to apply filters
            filter_lst: List of filter keys

        Returns:
            Array of maximum force values
        """
        arr = np.array([])
        for i in range(len(self)):
            fc1 = forcecurve()
            fc1.data = self[i]
            fc1.recover_force(ljp)
            data = fc1.get_prodata()["retract"]
            data_y = data["vDeflection"] * 1e12
            if len(fc1.data["peakindex"]) == 0:
                max_d = data_y[int(0.8 * len(data_y)) :].max()
            else:
                max_d = data_y[fc1.data["peakindex"]].max()
            if max_d < 0:
                max_d = 0
            arr = np.append(arr, max_d)
        return arr

    def resortForce(self, index_lst: list) -> bool:
        """Reorder force curves by index list.

        Args:
            index_lst: New order of indices

        Returns:
            True if successful
        """
        if len(index_lst) < max(index_lst) or len(self) != len(index_lst):
            return False
        lst = np.array(list(self.data["data.pkl"].keys()))[index_lst]
        lst = [(a, int(b)) for a, b in lst]
        dic = {}
        for k in lst:
            dic[k] = self.data["data.pkl"][k]
        self.data["data.pkl"] = dic
        self.savefile()
        return True

    def split_bypeakN(self) -> None:
        """Split archive by number of peaks."""
        fc = forcecurve()
        dic = {}
        pure_fname = os.path.splitext(self.fname)[0]
        for i, data in enumerate(self):
            fc.data = data
            peakN = fc.data["peakindex"]
            if peakN not in dic.keys():
                dic[peakN] = []
            dic[peakN].append(fc)
        for k, v in dic.items():
            fname = "{}-peakN-{}.DataYee-Force".format(pure_fname, k)
            with ZipFile(fname, "a", zipfile.ZIP_DEFLATED) as zips:
                for fc in v:
                    o = (
                        os.path.splitext(os.path.basename(fc.data["datamsg"][0]))[0]
                        + "-s-"
                        + str(fc.data["datamsg"][1])
                        + ".pkl"
                    )
                    pkl = pickle.dumps(fc.data)
                    zips.writestr(o, pkl)

    def split_DataYee(self, SplitDic: dict) -> None:
        """Split archive by cluster assignments.

        Args:
            SplitDic: Dictionary mapping cluster ID to curve indices
        """
        rawname = os.path.splitext(os.path.basename(self.fname))[0]
        dirname = os.path.join(os.path.dirname(self.fname), "clustering")
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        with ZipFile(self.fname, "r", zipfile.ZIP_DEFLATED) as zips:
            lst = copy.deepcopy(zips.namelist())
        with ZipFile(self.fname, "r", zipfile.ZIP_DEFLATED) as zips:
            for classindex, indexlst in SplitDic.items():
                outputname = os.path.join(
                    dirname, "{}-{}.{}".format(rawname, classindex, "DataYee-force")
                )
                if os.path.isfile(outputname):
                    os.remove(outputname)
                for index in indexlst:
                    arcname = lst[index]
                    with zips.open(arcname, "r") as f:
                        pkl = f.read()
                    with ZipFile(outputname, "a", zipfile.ZIP_DEFLATED) as zips1:
                        zips1.writestr(arcname, pkl)
