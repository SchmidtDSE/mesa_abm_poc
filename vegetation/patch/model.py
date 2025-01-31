import mesa
import mesa_geo as mg
import numpy as np
import shapely.geometry as sg
from shapely.ops import transform
import random
import json
from scipy.stats import poisson
from pyproj import Transformer
import logging

from vegetation.config.stages import LifeStage
from vegetation.patch.space import StudyArea, VegCell
from vegetation.patch.utils import transform_point_wgs84_utm, generate_point_in_utm
from vegetation.config.transitions import (
    JOTR_JUVENILE_AGE,
    JOTR_REPRODUCTIVE_AGE,
    JOTR_SEED_DISPERSAL_DISTANCE,
    JOTR_SEEDS_EXPECTED_VALUE,
    get_jotr_survival_rate,
    get_jotr_number_seeds,
    get_jotr_germination_rate,

)
from vegetation.config.paths import INITIAL_AGENTS_PATH
from vegetation.config.logging import (
    LogConfig,
    AgentLogger,
    SimLogger,
    AgentEventType,
    SimEventType,
)

JOTR_UTM_PROJ = "+proj=utm +zone=11 +ellps=WGS84 +datum=WGS84 +units=m +no_defs +north"
STD_INDENT = "    "


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

    def _update_life_stage(self):

        initial_life_stage = self.life_stage

        if self.life_stage == LifeStage.DEAD:
            return

        age = self.age if self.age else 0
        if age == 0:
            life_stage = LifeStage.SEED
        elif age > 0 and age <= JOTR_JUVENILE_AGE:
            life_stage = LifeStage.SEEDLING
        elif age >= JOTR_JUVENILE_AGE and age <= JOTR_REPRODUCTIVE_AGE:
            life_stage = LifeStage.JUVENILE
        else:
            life_stage = LifeStage.ADULT
        self.life_stage = life_stage

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

        # Find the underlying cell - it must exist, else raise an error
        intersecting_cell_filter = self.model.space.raster_layer.iter_neighbors(
            self.indices, moore=False, include_center=True, radius=0
        )
        intersecting_cell = next(intersecting_cell_filter)
        if not intersecting_cell:
            raise ValueError("No intersecting cell found")

        # add dummy survival rate such that variable always exist during debugging phase
        survival_rate = 0

        # Roll the dice to see if the agent survives
        dice_roll_zero_to_one = random.random()
        
        if self.life_stage == LifeStage.SEED:
            if self.age > 3:
                self.life_stage =LifeStage.DEAD
            else:
                germination_rate = get_jotr_germination_rate(self.age)  

                if dice_roll_zero_to_one < germination_rate:
                    self.life_stage = LifeStage.SEEDLING

        else:
            survival_rate = get_jotr_survival_rate(
                self.life_stage)

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
        if self.life_stage == LifeStage.ADULT:

            n_seeds = get_jotr_number_seeds(JOTR_SEEDS_EXPECTED_VALUE)

            self.agent_logger.log_agent_event(
                self, AgentEventType.ON_DISPERSE, context={"n_seeds": n_seeds}
            )

            self._disperse_seeds_in_landscape(n_seeds)

    

    


class Vegetation(mesa.Model):

    @property
    def sim_logger(self):
        if not hasattr(self, "_sim_logger"):
            self._sim_logger = SimLogger()
        return self._sim_logger

    def __init__(
        self,
        bounds,
        export_data=False,
        num_steps=20,
        management_planting_density=0.01,
        epsg=4326,
        log_config_path=None,
        log_level=None,
    ):
        super().__init__()

        # Initialize logging config first
        if log_config_path:
            LogConfig.initialize(log_config_path)

        # To get this set up, assume sim has logging.INFO level
        self.log_level = logging.INFO

        self.bounds = bounds
        self.num_steps = num_steps
        self.management_planting_density = management_planting_density
        self._on_start_executed = False

        # mesa setup
        self.space = StudyArea(bounds, epsg=epsg, model=self)
        self.datacollector = mesa.DataCollector(
            {
                "Mean Age": "mean_age",
                "N Agents": "n_agents",
                "N Seeds": "n_seeds",
                "N Seedlings": "n_seedlings",
                "N Juveniles": "n_juveniles",
                "N Adults": "n_adults",
                "% Refugia Cells Occupied": "pct_refugia_cells_occupied",
            }
        )

    def _on_start(self):

        self.sim_logger.log_sim_event(self, SimEventType.ON_START)

        self.space.get_elevation()
        self.space.get_refugia_status()

        with open(INITIAL_AGENTS_PATH, "r") as f:
            initial_agents_geojson = json.loads(f.read())

        self._add_agents_from_geojson(initial_agents_geojson)

        self._on_start_executed = True

    def _add_agents_from_geojson(self, agents_geojson):
        agents = mg.AgentCreator(JoshuaTreeAgent, model=self).from_GeoJSON(
            agents_geojson
        )

        # TODO: Find a way to update life stage on init
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/9
        # Since .from_GeoJSON() sets attributes after init, we call
        # _update_life_stage after init, but before we add to the grid
        self.agents.select(agent_type=JoshuaTreeAgent).do("_update_life_stage")

        self.space.add_agents(agents)
        self.update_metrics()

    # def add_agents_from_management_draw(event, geo_json, action):
    def add_agents_from_management_draw(self, *args, **kwargs):

        assert kwargs.get("action") == "create"
        management_area = kwargs.get("geo_json")

        outplanting_point_locations = self._generate_planting_points(management_area)

        self.sim_logger.log_sim_event(
            self,
            SimEventType.ON_MANAGE,
            context={"n_agents": len(outplanting_point_locations)},
        )

        for management_x_wgs84, management_y_wgs84 in outplanting_point_locations:

            # TODO: Vegetation model doesn't know its own CRS
            # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/26
            management_agent = JoshuaTreeAgent(
                model=self,
                geometry=sg.Point(management_x_wgs84, management_y_wgs84),
                crs="EPSG:4326",
                age=20,
                parent_id=None,
            )
            management_agent._update_life_stage()

            self.space.add_agents(management_agent)

    def _generate_planting_points(self, geo_json):
        # Convert GeoJSON to Shapely polygon
        coords = geo_json[0]["geometry"]["coordinates"][0]
        polygon = sg.Polygon(coords)

        # Get UTM zone from polygon centroid
        lon, lat = polygon.centroid.x, polygon.centroid.y
        wgs84_to_utm, utm_to_wgs84 = transform_point_wgs84_utm(lon, lat)

        # Project polygon to UTM
        utm_polygon = transform(wgs84_to_utm.transform, polygon)
        area = utm_polygon.area
        num_points = int(area * self.management_planting_density)

        points = []
        minx, miny, maxx, maxy = utm_polygon.bounds

        while len(points) < num_points:
            x_utm = np.random.uniform(minx, maxx)
            y_utm = np.random.uniform(miny, maxy)
            point_utm = sg.Point(x_utm, y_utm)

            if utm_polygon.contains(point_utm):
                management_x_wgs84, management_y_wgs84 = utm_to_wgs84.transform(
                    x_utm, y_utm
                )
                points.append((management_x_wgs84, management_y_wgs84))

        return points

    def update_metrics(self):
        # Mean age
        mean_age = self.agents.select(agent_type=JoshuaTreeAgent).agg("age", np.mean)
        self.mean_age = mean_age

        # Number of agents by life stage
        count_dict = (
            self.agents.select(agent_type=JoshuaTreeAgent).groupby("life_stage").count()
        )
        self.n_seeds = count_dict.get(LifeStage.SEED, 0)
        self.n_seedlings = count_dict.get(LifeStage.SEEDLING, 0)
        self.n_juveniles = count_dict.get(LifeStage.JUVENILE, 0)
        self.n_adults = count_dict.get(LifeStage.ADULT, 0)
        self.n_dead = count_dict.get(LifeStage.DEAD, 0)

        # Number of agents (JoshuaTreeAgent)
        n_agents = len(self.agents.select(agent_type=JoshuaTreeAgent))
        self.n_agents = n_agents - self.n_dead

        # Number of refugia cells occupied by JoshuaTreeAgents
        count_dict = (
            self.agents.select(agent_type=VegCell)
            .select(filter_func=lambda agent: agent.refugia_status)
            .groupby("occupied_by_jotr_agents")
            .count()
        )
        self.pct_refugia_cells_occupied = count_dict.get(True, 0) / (
            count_dict.get(True, 0) + count_dict.get(False, 0)
        )

    def step(self):

        if not self._on_start_executed:
            self._on_start()

        self.sim_logger.log_sim_event(self, SimEventType.ON_STEP)

        # Step agents
        self.agents.shuffle_do("step")
        self.update_metrics()

        # Collect data
        self.datacollector.collect(self)
