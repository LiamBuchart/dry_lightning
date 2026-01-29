"""
Utility functions for working with shapefiles and geospatial data.
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# Cache for loaded shapefiles to avoid reloading
_shapefile_cache = {}


def load_simplified_shapefile(shapefile_path, simplify_tolerance=0.01):
    """
    Load and simplify a shapefile for faster spatial operations.
    Results are cached to avoid reloading.
    
    Parameters
    ----------
    shapefile_path : str
        Path to the shapefile
    simplify_tolerance : float
        Tolerance for simplifying geometries (in degrees). 
        Higher values = more simplification = faster queries.
        Default 0.01 degrees ≈ 1.1 km at equator
    
    Returns
    -------
    geopandas.GeoDataFrame
        Simplified and cached geodataframe with spatial index
    """
    if shapefile_path not in _shapefile_cache:
        gdf = gpd.read_file(shapefile_path)
        
        # Fix any invalid geometries first
        gdf['geometry'] = gdf['geometry'].buffer(0)
        
        # Simplify geometries to reduce complexity (faster point-in-polygon checks)
        gdf['geometry'] = gdf['geometry'].simplify(simplify_tolerance)
        
        # Rebuild spatial index for faster queries
        gdf = gdf.reset_index(drop=True)
        _ = gdf.sindex
        
        _shapefile_cache[shapefile_path] = gdf
    
    return _shapefile_cache[shapefile_path]


def point_in_shapefile(shapefile_path, lat, lon, buffer_km=0, simplify_tolerance=0.01):
    """
    Check if a lat/lon point is inside any polygon in a shapefile.
    
    Optimized with geometry simplification, caching, and spatial indexing.
    Uses an approach similar to stations_in_ecozone for checking point intersection
    with optional buffering around the shapefile polygons.
    
    Handles both Polygon and MultiPolygon geometries.
    
    Parameters
    ----------
    shapefile_path : str
        Path to the shapefile
    lat : float
        Latitude of the point
    lon : float
        Longitude of the point
    buffer_km : float, optional
        Buffer distance in kilometers to expand the polygon boundaries (default: 0)
    simplify_tolerance : float, optional
        Tolerance for simplifying geometries in degrees (default: 0.01 ≈ 1.1 km).
        Only applied when loading shapefile for the first time.
    
    Returns
    -------
    bool
        True if the point is inside any polygon in the shapefile (or buffer), False otherwise
    
    Examples
    --------
    >>> is_inside = point_in_shapefile('canada_census.shp', 53.5, -113.5)
    >>> print(is_inside)
    True
    
    >>> is_inside_with_buffer = point_in_shapefile('ecozones.shp', 53.5, -113.5, buffer_km=250)
    >>> print(is_inside_with_buffer)
    True
    """
    # Load simplified and cached geodataframe
    gdf = load_simplified_shapefile(shapefile_path, simplify_tolerance)
    
    # Create a Point from the lat/lon coordinates (x, y = lon, lat)
    point = Point(lon, lat)
    
    # Validate point geometry
    if not point.is_valid:
        point = point.buffer(0)
    
    # Use spatial index to find candidate geometries
    try:
        # Try using sindex query with bounds
        candidates = list(gdf.sindex.query(point.bounds, predicate='intersects'))
    except (TypeError, AttributeError):
        # Fallback: use simpler approach with intersects
        candidates = list(gdf.geometry.intersects(point).to_numpy().nonzero()[0])
    
    if len(candidates) == 0:
        result = False
    else:
        # Check if point is actually contained in any candidate polygon
        result = gdf.geometry.iloc[candidates].contains(point).any()
    
    # If not found and buffer is specified, check buffered geometries (similar to stations_in_ecozone)
    if not result and buffer_km > 0:
        # Only buffer candidate geometries (more efficient)
        gdf_candidates = gdf.iloc[candidates] if len(candidates) > 0 else gdf
        gdf_candidates['geometry_buffered'] = gdf_candidates['geometry'].apply(
            lambda geom: geom.buffer(buffer_km / 111)  # Approximate conversion from km to degrees
        )
        # Check if point intersects with any buffered geometry
        result = gdf_candidates['geometry_buffered'].intersects(point).any()
    
    return result
