import random

import numpy as np
from pyproj import Transformer


def transform_point_wgs84_utm(lon: float, lat: float, utm_zone: int = None) -> tuple:
    """Transform single point between WGS84 and UTM"""
    if utm_zone is None:
        utm_zone = int((lon + 180) / 6) + 1
    utm_crs = f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs"

    wgs84_to_utm = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)
    utm_to_wgs84 = Transformer.from_crs(utm_crs, "EPSG:4326", always_xy=True)

    return wgs84_to_utm, utm_to_wgs84


def generate_point_in_utm(x_utm: float, y_utm: float, max_distance: float) -> tuple:
    """Generate random point within distance of UTM coordinates"""
    angle = random.uniform(0, 2 * np.pi)
    distance = random.uniform(0, max_distance)

    new_x = x_utm + distance * np.cos(angle)
    new_y = y_utm + distance * np.sin(angle)

    return new_x, new_y
