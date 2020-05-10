#!/usr/bin/env python3

import fsspec as fs
import xarray as xr

FLASK_LOCAL = "http://127.0.0.1:5000"
LOAD_ARRAY = False

ones_fs = fs.get_mapper(f"{FLASK_LOCAL}/generated-ones/")
ones_ds = xr.open_zarr(ones_fs)
print(ones_ds)
if LOAD_ARRAY:
    ones_da = ones_ds["ones"].load()
    print(ones_da)
