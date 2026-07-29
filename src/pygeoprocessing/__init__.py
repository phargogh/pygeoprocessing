"""pygeoprocessing: geoprocessing routines for GIS.

__init__ module imports all the geoprocessing functions into this namespace.
"""
import logging
import sys
import types
import os
import importlib
import functools

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version
    from importlib_metadata import PackageNotFoundError

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())  # silence logging by default

# these are bit masks for the known PyGeoprocessing types
UNKNOWN_TYPE = 0
RASTER_TYPE = 1
VECTOR_TYPE = 2

try:
    __version__ = version('pygeoprocessing')
except PackageNotFoundError:
    # package is not installed
    pass


def _lazy_import(modulename):
    """Lazily import a module.

    The returned module object will not actually be imported until a module
    attribute is accessed.

    Args:
        modulename (str): The name of the module to load.  If the modulename
            starts with a ".", it will be treated as a relative import.

    Returns:
        An ``importlib.util._LazyModule`` instance.
    """
    # Locate the module's specification.
    # Handle the case where a relative import is requested.
    package = None
    if modulename.startswith('.'):
        package = __package__
    spec = importlib.util.find_spec(modulename, package=package)
    if spec is None:
        raise ModuleNotFoundError(f"No module named '{module}'")

    # Wrap the existing loader with LazyLoader
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader

    # Create the module object from the modified spec
    module = importlib.util.module_from_spec(spec)

    # Cache it in sys.modules so future traditional imports pull this reference
    sys.modules[modulename] = module

    # Execute the module proxy shell
    loader.exec_module(module)
    return module


geoprocessing = _lazy_import(".geoprocessing")
_exposed_attrs = {
    ".geoprocessing": [
        "_assert_is_valid_pixel_size",
        "align_and_resize_raster_stack",
        "align_bbox",
        "array_equals_nodata",
        "build_overviews",
        "calculate_disjoint_polygon_set",
        "choose_dtype",
        "choose_nodata",
        "convolve_2d",
        "create_raster_from_bounding_box",
        "create_raster_from_vector_extents",
        "distance_transform_edt",
        "get_gis_type",
        "get_raster_info",
        "get_vector_info",
        "interpolate_points",
        "iterblocks",
        "mask_raster",
        "merge_bounding_box_list",
        "new_raster_from_base",
        "numpy_array_to_raster",
        "raster_calculator",
        "raster_map",
        "raster_reduce",
        "raster_to_numpy_array",
        "rasterize",
        "ReclassificationMissingValuesError",
        "reclassify_raster",
        "reproject_vector",
        "shapely_geometry_to_vector",
        "stitch_rasters",
        "transform_bounding_box",
        "warp_raster",
        "zonal_statistics",
    ],
    ".slurm_utils": [
        "log_warning_if_gdal_will_exhaust_slurm_memory",
    ],
    ".utils": [
         "GDALUseExceptions",
         "gdal_use_exceptions",
    ],
    ".geoprocessing_core": [
        "calculate_slope",
        "raster_band_percentile",
    ],
}
_reverse_module_map = {}  # funcname: modulename
__all__ = tuple()
for _modulename, _member_funcnames in _exposed_attrs.items():
    for _funcname in _member_funcnames:
        _reverse_module_map[_funcname] = _modulename
        __all__ += (_funcname,)

# Lazily load attributes that are defined in __all__.
def __getattr__(name: str):
    if name in __all__:
        package = None
        module = _reverse_module_map[name]
        if module.startswith('.'):
            package = __package__
        imported_module = importlib.import_module(module, package=package)
        return getattr(imported_module, name)
    raise AttributeError(name)


# Our lazy attribute loading means that items we want to lazily load won't
# be able to be inspected easily with dir().  Add them back.
def __dir__():
    _default_attrs = list(globals().keys())
    return sorted(_default_attrs + list(__all__))


def get_include():
    """Return the directory that includes the pygeoprocessing *.h header files.

    Returns:
        The string path to the header files location."""
    return os.path.join(os.path.dirname(__file__), 'extensions')
