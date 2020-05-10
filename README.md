# zarrflask

Dynamic zarr generation from xarray datasets

## About

This is a [Flask](https://flask.palletsprojects.com/) web application which dynamically generates and serves [Zarr](https://zarr.readthedocs.io/) from [xarray](https://xarray.pydata.org/) datasets.

The [Zarr specification](https://zarr.readthedocs.io/en/stable/spec/v2.html) is intentionally written so that "array store" is an interface, rather than a requirement on underlying implementation.
The zarr interface can be supplied using a HTTP API via a web server, rather than the typical approach of a bunch of files in a filesystem directory structure.

zarrflask generates Zarr data chunks and metadata objects as they are requested by HTTP clients.
This contrasts with the [xarray `to_zarr` function](https://xarray.pydata.org/en/stable/generated/xarray.Dataset.to_zarr.html) which writes the whole dataset to storage in one hit.

The underlying source for the xarray dataset being served is flexible - it could be:
- an in-memory numpy backed array
- a lazily loaded dask array aggregating multiple underlying netCDF files from [xarray's `open_mfdataset` function](https://xarray.pydata.org/en/stable/generated/xarray.open_mfdataset.html)
- a lazily computed dask array consisting of data loading plus calculations based on the data
- a large historical data store with templated metadata such as a [hypotheticube](https://medium.com/informatics-lab/hypothetical-datasets-70381cce8a9)

## Usage

Quick setup and demonstration using flask development server:

```sh
git clone https://github.com/tjtg/zarrflask.git zarrflask
cd zarrflask
pip install -r requirements.txt
flask run
# then in another terminal
python reader.py
```

To serve your own data instead of the built-in example datasets, add your xarray dataset to the `dsets` dictionary in the `initialise` function in `data.py`.

For anything other than toy/development usage, use of a multi-process production-quality WSGI server is recommended - see [Flask deployment documentation](https://flask.palletsprojects.com/en/1.1.x/deploying/) for a range of options such as gunicorn and uWSGI.

## Performance

There's not a lot of code here and nothing that takes much processing time - a few slicing operations and packing some values into metadata dicts, then conversion to JSON.

Response time is by far dominated by data retrieval time.
If that's in-memory numpy data, Flask response times are very fast, often under 1ms.
For dask-backed lazy data, response time is highly dependent on the dask data source.

The chunk size for arrays with more than two dimensions is configured to be quite small for demonstration purposes - see function `chunk_shape` in `endec.py` for details.
A potential future enhancement would be to handle dask-backed arrays separately and align the zarr chunks with dask so that there is a 1:1 relationship between the dask backend chunks and the HTTP-served chunks.

The flask built-in server warns:
> This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.

Flask's built-in server uses multiple python threads to process requests concurrently, but this is not a high performance solution.
In particular, there will be constraints with multithreaded access to netCDF/HDF5 files from a single process, even if those threads are only reading.
Use of a multi-process production-quality WSGI server is recommended - see [Flask deployment documentation](https://flask.palletsprojects.com/en/1.1.x/deploying/) for a range of options.

## Dependencies

Required:
- xarray - multidimensional data arrays with coordinates and metadata
- Flask - microframework for web applications

Note that the zarr library is not a required dependency - this code indendently produces responses that follow the zarr interface specification.

Optional libraries for `reader.py` example:
- zarr
- fsspec
- requests

Useful, but not required:
- netCDF4 - reading data from netCDF files
- dask - parallel and lazy array loading and computation

## Known issues

- There is currently no compression applied to data chunks. Applying a high-speed compressor such as lz4 or zstd would likely improve overall performance due to sending less data over the network, at the expense of a small amount of CPU server time.
- Data chunk responses are not streamed to the flask framework (and from there to the HTTP client). Large chunk responses will take up a corresponding amount of memory on the web server.
- Not all xarray or zarr datatypes are supported yet. The basics (floats, ints) work ok, but other less commonly used types will likely not work.
- There are currently no tests.
    - Since this code is intended to serve xarray datasets, a potential testing approach is to check that roundtripping via xarray's `open_zarr` function produces the same dataset as that served by zarrflask.

## License

[3-clause BSD License](./license.md)
