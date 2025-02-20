from __future__ import annotations

import mesa
import mesa_geo as mg
from shapely.geometry import Point

from vegetation.config.life_stages import LifeStage


class VegCell(mg.Cell):
    elevation: int | None
    refugia_status: bool = False
    jotr_max_life_stage: int | None

    def __init__(
        self,
        model,
        pos: mesa.space.Coordinate | None = None,
        indices: mesa.space.Coordinate | None = None,
    ):
        super().__init__(model, pos, indices)
        self._geometry = None

        self.elevation = None

        # TODO: Improve patch level tracking of JOTR agents
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/1
        # For now, this is somewhat of a hack to track which agents are present within a patch cell
        # This is something I suspect is an offshoot of my question posed to the mesa-geo team
        # (https://github.com/projectmesa/mesa-geo/issues/267), where the cell does not have a geometry
        # and thus I can't use the various geometry based intersection methods to find agents. My guess
        # is that this will either not work or be very slow, but itll get us started
        self.jotr_agents = []
        self.occupied_by_jotr_agents = False
        self.jotr_max_life_stage = 0

        # DEBUG: Test attribute to see how this interacts with Zarr groups / datasets
        self.test_attribute = 1

    @property
    def geometry(self):
        if not self._geometry:
            self._geometry = Point(
                self.indices * self.model.space.raster_layer._transform
            )
        return self._geometry

    def step(self):
        self.update_occupancy()

    def update_occupancy(self):
        # Very clunky way to exclude dead agents
        alive_patch_life_stages = [
            agent.life_stage
            for agent in self.jotr_agents
            if agent.life_stage != LifeStage.DEAD
        ]
        if alive_patch_life_stages:
            self.jotr_max_life_stage = max(alive_patch_life_stages)
            self.occupied_by_jotr_agents = True
        else:
            self.jotr_max_life_stage = None
            self.occupied_by_jotr_agents = False

    def add_agent_link(self, jotr_agent):
        if jotr_agent.life_stage and jotr_agent not in self.jotr_agents:
            self.jotr_agents.append(jotr_agent)
