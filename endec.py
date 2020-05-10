"""Helper functions to encode and decode data formats and handle chunking"""

from typing import Optional, Sequence, Tuple

import flask
import numpy as np


class NumpyJson(flask.json.JSONEncoder):
    """Sub-class of the flask JSON encoder to add handling of numpy objects"""

    def default(self, o: object) -> object:
        """Default encoding process for passed objects"""
        if isinstance(o, np.ndarray):
            converted = o.tolist()
            return converted
        elif isinstance(o, np.generic):
            converted = o.item()
            return converted
        return super().default(o)


def decode_chunk_path(chunk_path: str) -> Sequence[int]:
    """Split a string chunk path into integer indices"""
    parts = chunk_path.split(".")
    int_parts = [int(x) for x in parts]
    return int_parts


def chunk_shape(shape: Sequence[int]) -> Sequence[int]:
    """Given the array shape, return the shape of a single chunk"""
    if len(shape) <= 2:
        return [min(x, 1000) for x in shape]
    c_shape = []
    for i, length in enumerate(shape):
        if i <= 1:
            c_shape.append(1)
        else:
            c_shape.append(min(length, 100))
    return c_shape


def chunk_to_slice(
    chunk_idxs: Sequence[int], var_shape: Sequence[int]
) -> Tuple[slice, ...]:
    """Calculate array slice based on chunk size"""
    if len(var_shape) == 0:
        return tuple()
    chunk_s = chunk_shape(var_shape)
    slices = []
    for i, _ in enumerate(chunk_idxs):
        chunk_size = chunk_s[i]
        chunk_start = chunk_idxs[i] * chunk_size
        chunk_end = min(chunk_start + chunk_size, var_shape[i])
        slices.append(slice(chunk_start, chunk_end))
    return tuple(slices)


def pad_array(
    arr: np.ndarray, dest_shape: Sequence[int], offset: Optional[Sequence[int]] = None
) -> np.ndarray:
    """Pad an array to a larger size by adding zeros at the edges"""

    if arr.shape == ():
        arr = np.array([arr])
    if len(dest_shape) == 0:
        dest_shape = [1]
    if offset is None:
        offset = [0 for _ in dest_shape]
    dest = np.zeros(dest_shape, dtype=arr.dtype)
    insertion_slice = [
        slice(offset[dim], offset[dim] + arr.shape[dim]) for dim in range(arr.ndim)
    ]
    dest[tuple(insertion_slice)] = arr
    return dest
