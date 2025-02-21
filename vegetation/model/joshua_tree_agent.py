import mesa_geo as mg
import numpy as np
import shapely.geometry as sg
import random
import logging
import json
import mesa
from shapely.ops import transform

from vegetation.space.veg_cell import VegCell
from vegetation.space.study_area import StudyArea
from vegetation.config.life_stages import LifeStage
from vegetation.utils.spatial import transform_point_wgs84_utm, generate_point_in_utm
from vegetation.config.transitions import (
    JOTR_JUVENILE_AGE,
    JOTR_REPRODUCTIVE_AGE,
    JOTR_SEED_DISPERSAL_DISTANCE,
    JOTR_SEEDS_EXPECTED_VALUE_MAST,
    JOTR_SEEDS_EXPECTED_VALUE_NORMAL,
    JOTR_MAST_YEAR_PROB,
    JOTR_AGENT_FLOWERING_PROB,
    JOTR_SEED_MAX_AGE,
    JOTR_BASE_GERMINATION_RATE,
    JOTR_BASE_SURVIVAL_SEEDLING,
    JOTR_BASE_SURVIVAL_JUVENILE,
    JOTR_BASE_SURVIVAL_ADULT,
    JOTR_SEED_VIABILITY_LOSS,
    get_jotr_survival_rate,
    get_jotr_number_seeds,
    get_jotr_germination_rate,
)
from vegetation.logging.logging import (
    LogConfig,
    AgentLogger,
    SimLogger,
    AgentEventType,
    SimEventType,
)
from vegetation.config.global_paths import INITIAL_AGENTS_PATH


class JoshuaTreeAgent(mg.GeoAgent):
    @property
    def agent_logger(self):
        if not hasattr(self, "_agent_logger"):
            self._agent_logger = AgentLogger()
        return self._agent_logger

    def __init__(self, model, geometry, crs, age=None, parent_id=None, log_level=None):
        super().__init__(
            model=model,
            geometry=geometry,
            crs=crs,
        )

        self.age = age
        self.parent_id = parent_id
        self.life_stage = None
        self.has_flowered_previous_year = False
        # self.log_level = log_level

        # To get this set up, assume all agents have logging.INFO level
        self.log_level = logging.INFO

        # TODO: When we create the agent, we need to know its own indices relative
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/6
        # to the rasterlayer. This seems like very foundational mesa / mesa-geo stuff,
        # which should be handled by the GeoAgent or GeoBase, but the examples are
        # inconsistent. For now, invert the affine transformation to get the indices,
        # converting from geographic (lat, lon) to raster (col, row) coordinates

        self.float_indices = ~self.model.space.raster_layer._transform * (
            np.float64(geometry.x),
            np.float64(geometry.y),
        )

        # According to wang-boyu, mesa-geo maintainer:
        # pos = (x, y), with an origin at the lower left corner of the raster grid
        # indices = (row, col) format with an origin at the upper left corner of the raster grid
        # See https://github.com/projectmesa/mesa-geo/issues/267

        # pos = (np.float64(geometry.x), np.float64(geometry.y))
        # self._pos = pos

        self.indices = (
            int(self.float_indices[0]),
            self.model.space.raster_layer.height - int(self.float_indices[1]),
        )
        self._pos = (
            int(self.float_indices[0]),
            int(self.float_indices[1]),
        )

        self.agent_logger.log_agent_event(self, AgentEventType.ON_CREATE)
        self._link_underlying_cell()

        # TODO: Figure out how to set the life stage on init
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/3
        # Seems natural to set the life stage on init, but in
        # see lines 181-190 in mesa_geo/geoagent.py, the agents are instantiated before the
        # GeoAgent gets the attributes within the geojson, so we need to call _update_life_stage
        # after init when the age is known to the agent

        # self._update_life_stage()

    def _link_underlying_cell(self):
        intersecting_cell_filter = self.model.space.raster_layer.iter_neighbors(
            self.indices, moore=False, include_center=True, radius=0
        )
        try:
            self.intersecting_cell = next(intersecting_cell_filter)
            self.intersecting_cell.add_agent_link(self)

        except StopIteration:
            Warning(
                f"Agent is outside the boundary of the base raster layers ({self.model.space.bounds}) and will be removed: {self.geometry}"
            )
            self.remove()

    def _update_life_stage(self):
        initial_life_stage = self.life_stage

        if self.life_stage == LifeStage.DEAD:
            return

        age = self.age if self.age else 0

        # update purely age-driven transitions
        if age <= JOTR_SEED_MAX_AGE and self.life_stage != LifeStage.SEEDLING:
            self.life_stage = LifeStage.SEED
        elif age > JOTR_SEED_MAX_AGE and self.life_stage == LifeStage.SEED:
            self.life_stage = LifeStage.DEAD
        elif age >= JOTR_JUVENILE_AGE and age <= JOTR_REPRODUCTIVE_AGE:
            # uncomment to debug
            # print(f"stage is {self.life_stage} and age is {self.age}.")
            self.life_stage = LifeStage.JUVENILE
        elif age > JOTR_REPRODUCTIVE_AGE:
            self.life_stage = LifeStage.ADULT
        if initial_life_stage != self.life_stage:
            return True
        else:
            return False

    def _disperse_seeds_in_landscape(
        self, n_seeds, max_dispersal_distance=JOTR_SEED_DISPERSAL_DISTANCE
    ):
        if self.life_stage != LifeStage.ADULT:
            raise ValueError(
                f"Agent {self.unique_id} is not reproductive yet and cannot disperse seeds"
            )

        wgs84_to_utm, utm_to_wgs84 = transform_point_wgs84_utm(
            self.geometry.x, self.geometry.y
        )
        x_utm, y_utm = wgs84_to_utm.transform(self.geometry.x, self.geometry.y)

        for __seed_idx in np.arange(0, n_seeds):
            seed_x_utm, seed_y_utm = generate_point_in_utm(
                x_utm, y_utm, max_dispersal_distance
            )
            seed_x_wgs84, seed_y_wgs84 = utm_to_wgs84.transform(seed_x_utm, seed_y_utm)

            seed_agent = JoshuaTreeAgent(
                model=self.model,
                geometry=sg.Point(seed_x_wgs84, seed_y_wgs84),
                crs=self.crs,
                age=0,
                parent_id=self.unique_id,
            )
            seed_agent._update_life_stage()

            self.model.space.add_agents(seed_agent)

    def step(self):
        # Check if agent is dead - if yes, skip
        if self.life_stage == LifeStage.DEAD:
            return

        # Roll the dice to see if the agent survives
        dice_roll_zero_to_one = random.random()

        if self.life_stage == LifeStage.SEED:
            germination_rate = get_jotr_germination_rate()

            if dice_roll_zero_to_one < germination_rate:
                self.life_stage = LifeStage.SEEDLING

            else:
                dice_roll_zero_to_one = random.random()

                if dice_roll_zero_to_one < JOTR_SEED_VIABILITY_LOSS:
                    self.life_stage = LifeStage.DEAD

        else:
            survival_rate = get_jotr_survival_rate(self.life_stage)

            if dice_roll_zero_to_one < survival_rate:
                self.agent_logger.log_agent_event(
                    self,
                    AgentEventType.ON_SURVIVE,
                    context={"survival_rate": survival_rate},
                )
            else:
                self.agent_logger.log_agent_event(
                    self,
                    AgentEventType.ON_DEATH,
                    context={"survival_rate": survival_rate},
                )
                self.life_stage = LifeStage.DEAD

        # Increment age
        self.age += 1
        life_stage_promotion = self._update_life_stage()

        if life_stage_promotion:
            self.agent_logger.log_agent_event(self, AgentEventType.ON_TRANSITION)

        # Disperse
        if (self.life_stage == LifeStage.ADULT) and self.model.flowering_year:
            # Roll the dice to see if mast year
            dice_roll_zero_to_one = random.random()

            if dice_roll_zero_to_one < JOTR_AGENT_FLOWERING_PROB:
                n_seeds = get_jotr_number_seeds(JOTR_SEEDS_EXPECTED_VALUE_MAST)

                self.agent_logger.log_agent_event(
                    self, AgentEventType.ON_DISPERSE, context={"n_seeds": n_seeds}
                )

                self._disperse_seeds_in_landscape(n_seeds)
