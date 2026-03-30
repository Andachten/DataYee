"""Serialization utilities for safe data storage.

This module provides alternatives to pickle for security-sensitive serialization.
Supports JSON and msgpack formats.
"""

from __future__ import annotations

import json
import pickle
import zipfile
from pathlib import Path
from typing import Any, Optional
import numpy as np
import numpy.typing as npt


def numpy_to_list(arr: npt.NDArray[np.float64]) -> list:
    """Convert numpy array to list for JSON serialization.

    Args:
        arr: Numpy array

    Returns:
        Python list
    """
    return arr.tolist()


def list_to_numpy(lst: list) -> npt.NDArray[np.float64]:
    """Convert list back to numpy array.

    Args:
        lst: Python list

    Returns:
        Numpy array
    """
    return np.array(lst)


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy arrays and complex numbers."""

    def default(self, obj: Any) -> Any:
        """Encode special numpy types.

        Args:
            obj: Object to encode

        Returns:
            Encoded object
        """
        if isinstance(obj, np.ndarray):
            return {
                "__type": "ndarray",
                "data": obj.tolist(),
                "dtype": str(obj.dtype),
            }
        elif isinstance(obj, np.complexfloating):
            return {"__type": "complex", "real": obj.real, "imag": obj.imag}
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)


def numpy_decoder(obj: dict) -> Any:
    """Decode numpy types from JSON dict.

    Args:
        obj: Dictionary with encoded data

    Returns:
        Decoded object
    """
    if "__type" in obj:
        if obj["__type"] == "ndarray":
            return np.array(obj["data"], dtype=obj["dtype"])
        elif obj["__type"] == "complex":
            return complex(obj["real"] + obj["imag"] * 1j)
    return obj


def save_json(data: dict, filepath: str | Path) -> None:
    """Save data to JSON file.

    Args:
        data: Dictionary to save
        filepath: Output file path
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, cls=NumpyEncoder, indent=2)


def load_json(filepath: str | Path) -> dict:
    """Load data from JSON file.

    Args:
        filepath: Input file path

    Returns:
        Loaded dictionary
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f, object_hook=numpy_decoder)


def save_compressed_pickle(data: dict, filepath: str | Path) -> None:
    """Save data using compressed pickle in a ZIP archive.

    This is the format used by DataYee archives (.DataYee-force).

    Args:
        data: Dictionary to save
        filepath: Output file path
    """
    with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zips:
        for key, value in data.items():
            zips.writestr(key, pickle.dumps(value))


def load_compressed_pickle(filepath: str | Path) -> dict:
    """Load data from compressed pickle ZIP archive.

    Args:
        filepath: Input file path

    Returns:
        Loaded dictionary
    """
    data = {}
    with zipfile.ZipFile(filepath, "r", zipfile.ZIP_DEFLATED) as zips:
        for fname in zips.namelist():
            with zips.open(fname) as f:
                data[fname] = pickle.load(f)
    return data


def compress_numpy_arrays(data: dict) -> dict:
    """Compress numpy arrays in a dictionary using LZMA.

    Args:
        data: Dictionary potentially containing numpy arrays

    Returns:
        Dictionary with compressed arrays
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, np.ndarray):
            dtype = value.dtype
            if dtype == np.float64:
                dtype_str = "<f8"
            elif dtype == np.float32:
                dtype_str = "<f4"
            else:
                dtype_str = str(dtype)
            compressed = __import__("lzma").compress(value.astype(dtype_str).tobytes())
            result[key] = (compressed, dtype_str)
        elif isinstance(value, dict):
            result[key] = compress_numpy_arrays(value)
        else:
            result[key] = value
    return result


def decompress_numpy_arrays(data: dict) -> dict:
    """Decompress numpy arrays in a dictionary.

    Args:
        data: Dictionary with compressed arrays

    Returns:
        Dictionary with decompressed arrays
    """
    import lzma

    result = {}
    for key, value in data.items():
        if isinstance(value, tuple) and len(value) == 2:
            if isinstance(value[0], bytes) and isinstance(value[1], str):
                compressed, dtype_str = value
                result[key] = np.frombuffer(
                    lzma.decompress(compressed), np.dtype(dtype_str.replace("<f8", "<f8"))
                )
                continue
        elif isinstance(value, dict):
            result[key] = decompress_numpy_arrays(value)
        else:
            result[key] = value
    return result
