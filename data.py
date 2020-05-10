"""
Data definition for zarrflask server

These datasets are simple examples. For use with data files, modify the
initialise function to load those datasets as appropriate. The datasets
can be dask-backed lazy/delayed data to avoid requiring memory for the
full size of the dataset.
"""

import dask.array as da
import numpy as np
import xarray as xr

dsets = {}


def initialise():
    global dsets

    # This dataset is real/in-memory numpy data
    ones_da = xr.DataArray(
        data=np.ones((101, 101, 101), dtype=np.float32),
        dims=("x", "y", "z"),
        coords={
            "x": np.linspace(0.0, 1.0, num=101, dtype=np.float64),
            "y": np.linspace(-100.0, 0.0, num=101, dtype=np.float64),
            "z": np.linspace(0.0, 1000.0, num=101, dtype=np.float64),
        },
        attrs={"abc": "xyz", "integer": 1, "floating": 1.5},
    )
    dsets["generated-ones"] = xr.Dataset(
        {"ones": ones_da}, attrs={"global-attributes": "yes"}
    )
    random_float = xr.DataArray(
        da.random.uniform(low=0.0, high=1.0, size=(40000, 40000), chunks=(100, 100))
    )
    random_int = xr.DataArray(
        da.random.randint(low=0, high=100, size=(40000, 40000), chunks=(512, 512))
    )
    dsets["generated-random"] = xr.Dataset({"float": random_float, "int": random_int})
