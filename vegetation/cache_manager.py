import os
import time
import hashlib
import numpy as np
import stackstac
import mesa_geo as mg
from functools import cached_property
from pystac_client import Client as PystacClient
import planetary_computer
import logging

from vegetation.config.paths import DEM_STAC_PATH, LOCAL_STAC_CACHE_FSTRING
from vegetation.config.aoi import TST_JOTR_BOUNDS
from vegetation.patch.model import Vegetation


class CacheManager:
    def __init__(self, bounds, epsg, model):
        self.bounds = bounds
        self.epsg = epsg
        self.model = model
        self.bounds_md5 = hashlib.md5(str(bounds).encode()).hexdigest()
        self.local_cache_path_fstring = LOCAL_STAC_CACHE_FSTRING

    @cached_property
    def pystac_client(self):
        return PystacClient.open(
            DEM_STAC_PATH, modifier=planetary_computer.sign_inplace
        )

    @property
    def _cache_paths(self) -> dict:
        cache_dict = {
            "elevation": self.local_cache_path_fstring.format(
                band_name="elevation",
                bounds_md5=self.bounds_md5,
            ),
        }
        return cache_dict

    @property
    def _docker_host_cache_paths(self) -> dict:
        docker_host_cache_dict = {}
        if os.getenv("DOCKER_HOST_STAC_CACHE_FSTRING"):
            docker_host_cache_dict["elevation"] = os.getenv(
                "DOCKER_HOST_STAC_CACHE_FSTRING"
            ).format(
                band_name="elevation",
                bounds_md5=self.bounds_md5,
            )
        return docker_host_cache_dict

    def get_elevation_from_stac(self):

        logging.debug("Collecting STAC Items for elevation")
        items_generator = self.pystac_client.search(
            collections=["cop-dem-glo-30"],
            bbox=self.bounds,
        ).items()

        items = [item for item in items_generator]
        logging.debug(f"Found {len(items)} items")

        elevation = stackstac.stack(
            items=items,
            assets=["data"],
            bounds=self.bounds,
            epsg=self.epsg,
        )

        n_not_nan = np.unique(elevation.count(dim="time"))
        if not n_not_nan == [1]:
            raise ValueError(
                f"Some cells have no, or duplicate, elevation data. Unique number of non-nan values: {n_not_nan}"
            )

        elevation = elevation.median(dim="time")

        return elevation

    def populate_elevation_cache_if_not_exists(self):

        elevation_cache_path = self._cache_paths["elevation"]

        if os.path.exists(elevation_cache_path):
            logging.debug(f"Local elevation cache found: {elevation_cache_path}")
            return

        logging.warning("No local cache found, downloading elevation from STAC")
        time_at_start = time.time()

        elevation = self.get_elevation_from_stac()

        __elevation_bands, elevation_height, elevation_width = elevation.shape

        elevation_layer = mg.RasterLayer(
            model=self.model,
            height=elevation_height,
            width=elevation_width,
            total_bounds=self.bounds,
            crs=f"epsg:{self.epsg}",
        )

        elevation_layer.apply_raster(
            data=elevation,
            attr_name="elevation",
        )

        logging.debug(f"Saving elevation to local cache: {elevation_cache_path}")
        os.makedirs(os.path.dirname(elevation_cache_path), exist_ok=True)
        elevation_layer.to_file(elevation_cache_path)

        if os.getenv("DOCKER_HOST_STAC_CACHE_FSTRING"):

            docker_host_elevation_cache_path = self._docker_host_cache_paths[
                "elevation"
            ]
            os.makedirs(
                os.path.dirname(docker_host_elevation_cache_path), exist_ok=True
            )

            logging.debug(
                f"Also saving elevation to Docker host cache (to speed up cache build later on this machine): {docker_host_elevation_cache_path}"
            )
            elevation_layer.to_file(docker_host_elevation_cache_path)

        logging.debug(f"Downloaded elevation in {time.time() - time_at_start} seconds")


if __name__ == "__main__":
    vegetation_model = Vegetation(bounds=TST_JOTR_BOUNDS)
    cache_manager = CacheManager(TST_JOTR_BOUNDS, 4326, vegetation_model)
    cache_manager.populate_elevation_cache_if_not_exists()
