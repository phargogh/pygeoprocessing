import logging
import os
import time

import line_profiler
import numpy
import pygeoprocessing
import pygeoprocessing.routing
from osgeo import osr
from pygeoprocessing import geoprocessing

logging.basicConfig(level=logging.INFO)
_DEFAULT_ORIGIN = (444720, 3751320)
_DEFAULT_PIXEL_SIZE = (30, -30)
_DEFAULT_EPSG = 3116
FNODATA = float(numpy.finfo(numpy.float32).min)
BNODATA = 255
ASTORIA_DEM = (
    "/Users/jdouglass/Downloads/2022-05-16-astoria-ndr-troubleshooting/"
    "workspace/intermediate_outputs/cache_dir/filled_dem_regular.tif")
GURA_DEM = (
    "/Users/jdouglass/workspace/natcap/invest/data/invest-sample-data/"
    "RouteDEM/DEM_gura.tif")

numpy.set_printoptions(precision=4)

def _array_to_raster(
        base_array, target_nodata, target_path,
        creation_options=geoprocessing.DEFAULT_GTIFF_CREATION_TUPLE_OPTIONS[1],
        pixel_size=_DEFAULT_PIXEL_SIZE,
        projection_epsg=_DEFAULT_EPSG,
        origin=_DEFAULT_ORIGIN):
    """Passthrough to pygeoprocessing.array_to_raster."""
    projection = osr.SpatialReference()
    projection_wkt = None
    if projection_epsg is not None:
        projection.ImportFromEPSG(projection_epsg)
        projection_wkt = projection.ExportToWkt()
    pygeoprocessing.numpy_array_to_raster(
        base_array, target_nodata, pixel_size, origin, projection_wkt,
        target_path, raster_driver_creation_tuple=('GTiff', creation_options))


def rafa_test():
    workspace = 'rafa-decayed-accum-workspace'
    if not os.path.exists(workspace):
        os.mkdir(workspace)
    flow_dir_path = os.path.join(workspace, 'flow_dir.tif')
    _array_to_raster(
        numpy.array([[BNODATA, 0, 0, 0, 0]], dtype=numpy.uint8),
        BNODATA, flow_dir_path)

    flow_accum_path = os.path.join(workspace, 'flow_accum.tif')

    pygeoprocessing.routing.flow_accumulation_d8(
        (flow_dir_path, 1), flow_accum_path)
    print("Regular flow accumulation:          ",
          pygeoprocessing.raster_to_numpy_array(flow_accum_path))

    pygeoprocessing.routing.flow_accumulation_d8(
        (flow_dir_path, 1), flow_accum_path, custom_decay_factor=0.5)
    print("Decayed(const) flow accumulation:   ",
          pygeoprocessing.raster_to_numpy_array(flow_accum_path))

    decay_factor_path = os.path.join(workspace, 'decay_factor.tif')
    _array_to_raster(
        numpy.array([[FNODATA, 0.5, 0.5, 0.5, 0.5]], dtype=numpy.float32),
        FNODATA, decay_factor_path)
    pygeoprocessing.routing.flow_accumulation_d8(
        (flow_dir_path, 1), flow_accum_path,
        custom_decay_factor=(decay_factor_path, 1))
    print("Decayed(raster1) flow accumulation: ",
          pygeoprocessing.raster_to_numpy_array(flow_accum_path))

    decay_factor_path = os.path.join(workspace, 'decay_factor2.tif')
    _array_to_raster(
        numpy.array([[FNODATA, 0.5, 0.4, 0.3, 0.2]], dtype=numpy.float32),
        FNODATA, decay_factor_path)
    pygeoprocessing.routing.flow_accumulation_d8(
        (flow_dir_path, 1), flow_accum_path,
        custom_decay_factor=(decay_factor_path, 1))
    print("Decayed(raster2) flow accumulation: ",
          pygeoprocessing.raster_to_numpy_array(flow_accum_path))


def joining_upstream_flow_test():
    workspace = 'rafa-joining-upstream-flow-workspace'
    if not os.path.exists(workspace):
        os.mkdir(workspace)
    flow_dir_path = os.path.join(workspace, 'flow_dir.tif')
    _array_to_raster(
        numpy.array([
            [BNODATA, 0, 0, 0, 0],
            [BNODATA, 0, 0, 0, 2]], dtype=numpy.uint8),
        BNODATA, flow_dir_path)

    flow_accum_path = os.path.join(workspace, 'flow_accum.tif')

    pygeoprocessing.routing.flow_accumulation_d8(
        (flow_dir_path, 1), flow_accum_path)
    print("Regular flow accumulation:\n",
          pygeoprocessing.raster_to_numpy_array(flow_accum_path))


def dem_test(filled_dem_path, name, n=5):
    workspace = f'weighted_flow_dir_{name}'
    if not os.path.exists(workspace):
        os.mkdir(workspace)
    total_time = 0
    flow_dir_path = os.path.join(workspace, 'd8_flow_dir_path.tif')
    pygeoprocessing.routing.flow_dir_d8(
        (filled_dem_path, 1), flow_dir_path)
    target_flow_accum_path = os.path.join(
        workspace, 'd8_flow_accum_nodecay.tif')
    for _ in range(n):
        if os.path.exists(target_flow_accum_path):
            os.remove(target_flow_accum_path)

        start_time = time.time()
        pygeoprocessing.routing.flow_accumulation_d8(
            (flow_dir_path, 1), target_flow_accum_path)
        end_time = time.time()
        total_time += (end_time - start_time)

    print(f"Mean time per run (no decay): {total_time/n}s")

    target_flow_accum_path = os.path.join(
        workspace, 'd8_flow_accum_decay.tif')
    for _ in range(n):
        if os.path.exists(target_flow_accum_path):
            os.remove(target_flow_accum_path)

        start_time = time.time()
        profile = line_profiler.LineProfiler(
            pygeoprocessing.routing.flow_accumulation_d8)
        profile.runcall(
            pygeoprocessing.routing.flow_accumulation_d8,
            (flow_dir_path, 1), target_flow_accum_path,
            custom_decay_factor=0.5)
        profile.print_stats()
        end_time = time.time()
        total_time += (end_time - start_time)

    print(f"Mean time per run (w/ decay): {total_time/n}s")



if __name__ == '__main__':
    rafa_test()
    joining_upstream_flow_test()
    #dem_test(ASTORIA_DEM, 'astoria', 5)
    dem_test(GURA_DEM, 'gura', 5)
    #nonmatching()
