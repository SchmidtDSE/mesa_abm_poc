from __future__ import annotations

import mesa_geo as mg
import numpy as np
import os
import hashlib
import logging

from vegetation.config.global_paths import LOCAL_STAC_CACHE_FSTRING


class StudyArea(mg.GeoSpace):
    def __init__(self, bounds, epsg, model):
        super().__init__(crs=f"epsg:{epsg}")
        self.bounds = bounds
        self.model = model
        self.epsg = epsg

        # For local development, we want to cache the STAC data so we don't
        # have to download it every time. This hash is used to uniquely identify
        # the bounds of the study area, so that we can grab if we already have it
        self.bounds_md5 = hashlib.md5(str(bounds).encode()).hexdigest()
        self.local_stac_cache_fstring = LOCAL_STAC_CACHE_FSTRING

    @property
    def _cache_paths(self) -> dict:
        cache_dict = {
            "elevation": self.local_stac_cache_fstring.format(
                band_name="elevation",
                bounds_md5=self.bounds_md5,
            ),
        }
        return cache_dict

    def get_elevation(self):
        elevation_cache_path = self._cache_paths["elevation"]

        if os.path.exists(elevation_cache_path):
            logging.info(f"Loading elevation from local cache: {elevation_cache_path}")

            try:
                elevation_layer = mg.RasterLayer.from_file(
                    raster_file=elevation_cache_path,
                    model=self.model,
                    cell_cls=VegCell,
                    attr_name="elevation",
                )
            except Exception as e:
                logging.warning(
                    f"Failed to load elevation from local cache ({elevation_cache_path}): {e}"
                )
                raise e

        else:
            raise ValueError("No local cache found for elevation data")

        super().add_layer(elevation_layer)

    def get_refugia_status(self):
        elevation_array = self.raster_layer.get_raster("elevation")
        ninetyfive_percentile = np.percentile(elevation_array, 95)
        refugia = elevation_array > ninetyfive_percentile

        self.raster_layer.apply_raster(
            data=refugia,
            attr_name="refugia_status",
        )
        super().add_layer(self.raster_layer)

    @property
    def raster_layer(self):
        return self.layers[0]

    @raster_layer.setter
    def raster_layer(self, value):
        if self.layers:
            self.layers[0] = value
        else:
            self.layers.append(value)

    def is_at_boundary(self, row_idx, col_idx):
        return (
            row_idx == 0
            or row_idx == self.raster_layer.height
            or col_idx == 0
            or col_idx == self.raster_layer.width
        )
