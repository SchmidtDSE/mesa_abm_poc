from __future__ import annotations

import mesa
import mesa_geo as mg
import numpy as np
import stackstac
from pystac_client import Client as PystacClient
import planetary_computer
import random
import os
import hashlib
import logging
import time
from functools import cached_property

from vegetation.config.stages import LifeStage
from vegetation.config.paths import LOCAL_STAC_CACHE_FSTRING

# from patch.model import JoshuaTreeAgent
# import rioxarray as rxr

# DEM_STAC_PATH = "https://planetarycomputer.microsoft.com/api/stac/v1/"
# LOCAL_STAC_CACHE_FSTRING = "/tmp/local_dev_data/{band_name}_{bounds_md5}.tif"
# SAVE_LOCAL_STAC_CACHE = True


class VegCell(mg.Cell):
    elevation: int | None
    aridity: int | None
    refugia_status: bool = False

    def __init__(
        self,
        model,
        pos: mesa.space.Coordinate | None = None,
        indices: mesa.space.Coordinate | None = None,
    ):
        super().__init__(model, pos, indices)
        self.elevation = None
        self.aridity = None

        # TODO: Improve patch level tracking of JOTR agents
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/1
        # For now, this is somewhat of a hack to track which agents are present within a patch cell
        # This is something I suspect is an offshoot of my question posed to the mesa-geo team
        # (https://github.com/projectmesa/mesa-geo/issues/267), where the cell does not have a geometry
        # and thus I can't use the various geometry based intersection methods to find agents. My guess
        # is that this will either not work or be very slow, but itll get us started
        self.jotr_agents = []
        self.occupied_by_jotr_agents = False

    def step(self):
        # Right now, this cell is being updated by the JOTR agent step, but it probably shouldn't be
        self.update_occupancy()
        pass

    def update_occupancy(self):
        # Very clunky way to exclude dead agents
        alive_jotr_agents = [
            agent for agent in self.jotr_agents if agent.life_stage != LifeStage.DEAD
        ]
        self.occupied_by_jotr_agents = True if len(alive_jotr_agents) > 0 else False

    def add_agent_link(self, jotr_agent):
        if jotr_agent.life_stage and jotr_agent not in self.jotr_agents:
            self.jotr_agents.append(jotr_agent)


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
            print(f"Loading elevation from local cache: {elevation_cache_path}")

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

    def get_aridity(self):

        # TODO: Use something axtually real, but for now, assume this is an
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/8
        # positive relationship with elevation, with a little noise. This is
        # smelly because it relies on elevation being set first, but it's
        # a placeholder for now
        elevation_array = self.raster_layer.get_raster("elevation")
        inverse_elevation = np.array(elevation_array + random.uniform(-300, 300))

        self.raster_layer.apply_raster(
            data=inverse_elevation,
            attr_name="aridity",
        )
        super().add_layer(self.raster_layer)

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
