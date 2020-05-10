"""Flask app to serve xarray datasets as zarr"""

import itertools
import time

from flask import Flask, abort, g, render_template

import data
import endec
from data import dsets

app = Flask("zarrflask")
app.json_encoder = endec.NumpyJson


@app.before_first_request
def initialise_data():
    """Initialise sample data arrays"""
    data.initialise()


@app.before_request
def before():
    """Record time request arrived for performance measurement use"""
    g.request_start_time = time.perf_counter()


@app.after_request
def after(response):
    """Log request timing"""
    response_time = (time.monotonic() - g.request_start_time) * 1000.0
    app.logger.debug(f"{response_time:.2f}ms")
    return response


@app.route("/")
def index():
    dset_list = sorted(list(dsets.keys()))
    dset_list = [f"{x}/" for x in dset_list]
    return render_template("directory.html", components=dset_list)


@app.route("/favicon.ico")
def favicon():
    abort(404)
    return


@app.route("/<string:dataset>/")
def dataset_root(dataset: str) -> str:
    if dataset not in dsets.keys():
        abort(404)
        return
    data_var_names = list(dsets[dataset].data_vars) + list(dsets[dataset].coords)
    data_var_names = [f"{x}/" for x in data_var_names]
    data_var_names.append(".zgroup")
    data_var_names.append(".zattrs")
    data_var_names.append(".zmetadata")
    return render_template("directory.html", components=sorted(data_var_names))


@app.route("/<string:dataset>/.zgroup")
def dataset_group(dataset: str) -> dict:
    if dataset not in dsets.keys():
        abort(404)
        return
    zgroup = {"zarr_format": 2}
    return zgroup


@app.route("/<string:dataset>/.zattrs")
def dataset_attrs(dataset: str) -> dict:
    if dataset not in dsets.keys():
        abort(404)
        return
    zattrs = dict(dsets[dataset].attrs)
    return zattrs


@app.route("/<string:dataset>/.zmetadata")
def dataset_meta(dataset: str):
    if dataset not in dsets.keys():
        abort(404)
        return
    mdata = {"zarr_consolidated_format": 1, "metadata": {}}
    mdata["metadata"][".zattrs"] = dataset_attrs(dataset)
    mdata["metadata"][".zgroup"] = dataset_group(dataset)
    for var in list(dsets[dataset].data_vars) + list(dsets[dataset].coords):
        var_zarray = dataset_var_zarray(dataset, var)
        mdata["metadata"][f"{var}/.zarray"] = var_zarray
        var_zattrs = dataset_var_zattrs(dataset, var)
        mdata["metadata"][f"{var}/.zattrs"] = var_zattrs
    return mdata


@app.route("/<string:dataset>/<string:var>/")
def dataset_var(dataset: str, var: str):
    if dataset not in dsets.keys():
        abort(404)
        return
    if var not in dsets[dataset].keys():
        abort(404)
        return
    chunk_names = []
    var_shape = dsets[dataset][var].shape
    if var_shape == ():
        var_shape = (1,)
    chunk_max = endec.max_chunk_size(dsets[dataset][var].shape)
    number_of_chunks = [x // chunk_max for x in var_shape]
    ranges = [range(x + 1) for x in number_of_chunks]
    chunk_tuples = itertools.product(*ranges)
    for t in chunk_tuples:
        chunk_strs = [str(x) for x in t]
        chunk_names.append(".".join(chunk_strs))
    chunk_names.append(".zarray")
    chunk_names.append(".zattrs")
    chunk_names = sorted(chunk_names)
    return render_template("directory.html", components=chunk_names)


@app.route("/<string:dataset>/<string:var>/.zarray")
def dataset_var_zarray(dataset: str, var: str):
    if dataset not in dsets.keys():
        abort(404)
        return
    if var not in dsets[dataset].keys():
        abort(404)
        return
    arr_dtype = dsets[dataset][var].dtype
    arr_shape = dsets[dataset][var].shape
    if arr_dtype.kind == "f":
        fill_val = "NaN"
    else:
        fill_val = None
    zarray = {
        "zarr_format": 2,
        "order": "C",
        "filters": None,
        "fill_value": fill_val,
        "compressor": None,
        "dtype": arr_dtype.str,
        "shape": arr_shape,
        "chunks": endec.chunk_shape(arr_shape),
    }
    return zarray


@app.route("/<string:dataset>/<string:var>/.zattrs")
def dataset_var_zattrs(dataset: str, var: str):
    if dataset not in dsets.keys():
        abort(404)
        return
    if var not in dsets[dataset].keys():
        abort(404)
        return
    zattrs = dict(dsets[dataset][var].attrs)
    zattrs["_ARRAY_DIMENSIONS"] = list(dsets[dataset][var].dims)
    return zattrs


@app.route("/<string:dataset>/<string:var>/<string:chunk>")
def dataset_var_chunk(dataset: str, var: str, chunk: str):
    if dataset not in dsets.keys():
        abort(404)
        return
    if var not in dsets[dataset].keys():
        abort(404)
        return
    chunk_idxs = endec.decode_chunk_path(chunk)
    var_shape = dsets[dataset][var].shape
    slices = endec.chunk_to_slice(chunk_idxs, var_shape)
    var_slice = dsets[dataset][var].data[slices]
    required_shape = endec.chunk_shape(var_shape)
    pad_slice = endec.pad_array(var_slice, required_shape)
    pad_bytes = pad_slice.tobytes("C")
    return pad_bytes
