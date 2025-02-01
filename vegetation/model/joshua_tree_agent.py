import mesa_geo as mg
import numpy as np
import shapely.geometry as sg
import random
from scipy.stats import poisson
import logging

from vegetation.config.life_stages import LifeStage
from vegetation.utils.spatial import transform_point_wgs84_utm, generate_point_in_utm
from vegetation.config.transitions import (
    JOTR_JUVENILE_AGE,
    JOTR_REPRODUCTIVE_AGE,
    JOTR_ADULT_AGE,
    JOTR_SEED_DISPERSAL_DISTANCE,
    get_jotr_emergence_rate,
    get_jotr_survival_rate,
    get_jotr_breeding_poisson_lambda,
)
from vegetation.logging.logging import (
    AgentLogger,
    AgentEventType,
)


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

        # TODO: Figure out how to set the life stage on init
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/3
        # Seems natural to set the life stage on init, but in
        # see lines 181-190 in mesa_geo/geoagent.py, the agents are instantiated before the
        # GeoAgent gets the attributes within the geojson, so we need to call _update_life_stage
        # after init when the age is known to the agent

        # self._update_life_stage()

    def step(self):

        # Check if agent is dead - if yes, skip
        if self.life_stage == LifeStage.DEAD:
            return

        # Find the underlying cell - it must exist, else raise an error
        intersecting_cell_filter = self.model.space.raster_layer.iter_neighbors(
            self.indices, moore=False, include_center=True, radius=0
        )
        intersecting_cell = next(intersecting_cell_filter)
        if not intersecting_cell:
            raise ValueError("No intersecting cell found")

        # If seed, get emergence rate, if not, get survival rate
        if self.life_stage == LifeStage.SEED:
            survival_rate = get_jotr_emergence_rate(intersecting_cell.aridity)
        else:
            survival_rate = get_jotr_survival_rate(
                self.life_stage,
                intersecting_cell.aridity,
                0,  # Assume no nurse plants for now
            )

        # Roll the dice to see if the agent survives
        dice_roll_zero_to_one = random.random()

        # Check survival, comparing dice roll to survival rate
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
        # Update underlying patch
        intersecting_cell.add_agent_link(self)

        # Disperse
        if self.life_stage == LifeStage.BREEDING:

            jotr_breeding_poisson_lambda = get_jotr_breeding_poisson_lambda(
                intersecting_cell.aridity
            )
            n_seeds = poisson.rvs(jotr_breeding_poisson_lambda)

            self.agent_logger.log_agent_event(
                self, AgentEventType.ON_DISPERSE, context={"n_seeds": n_seeds}
            )

            self._disperse_seeds(n_seeds)

    def _update_life_stage(self):

        initial_life_stage = self.life_stage

        if self.life_stage == LifeStage.DEAD:
            return

        age = self.age if self.age else 0
        if age == 0:
            life_stage = LifeStage.SEED
        elif age > 0 and age <= JOTR_JUVENILE_AGE:
            life_stage = LifeStage.SEEDLING
        elif age >= JOTR_JUVENILE_AGE and age <= JOTR_ADULT_AGE:
            life_stage = LifeStage.JUVENILE
        elif age > JOTR_ADULT_AGE and age < JOTR_REPRODUCTIVE_AGE:
            life_stage = LifeStage.ADULT
        else:
            life_stage = LifeStage.BREEDING
        self.life_stage = life_stage

        if initial_life_stage != self.life_stage:
            return True
        else:
            return False

    def _disperse_seeds(
        self, n_seeds, max_dispersal_distance=JOTR_SEED_DISPERSAL_DISTANCE
    ):
        if self.life_stage != LifeStage.BREEDING:
            raise ValueError(
                f"Agent {self.unique_id} is not breeding and cannot disperse seeds"
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
