import mesa
import mesa_geo as mg
import numpy as np
import shapely.geometry as sg
from shapely.ops import transform
import json
import logging

from vegetation.config.stages import LifeStage
from vegetation.space.veg_cell import StudyArea, VegCell
from vegetation.utils.spatial import transform_point_wgs84_utm
from vegetation.config.paths import INITIAL_AGENTS_PATH
from vegetation.config.logging import (
    LogConfig,
    SimLogger,
    SimEventType,
)
from vegetation.utils.zarr_manager import (
    get_array_from_nested_cell_list,
)
from vegetation.model.joshua_tree_agent import JoshuaTreeAgent
from vegetation.utils.zarr_manager import ZarrManager

ZARR_FILENAME = "vegetation.zarr"
TEST_RUN_PARAMETERS = {
    "seedling_mortality_rate": 0.1,
    "juvenile_mortality_rate": 0.5,
}


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
        attrs_to_save=[],
        zarr_group_name=None,
    ):
        super().__init__()

        # Initialize logging config first
        if log_config_path:
            LogConfig.initialize(log_config_path)

        if not log_level:
            self.log_level = logging.INFO
        else:
            self.log_level = log_level

        self.bounds = bounds
        self.num_steps = num_steps
        self.management_planting_density = management_planting_density
        self._on_start_executed = False
        self.sim_idx = 1

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
                "N Breeding": "n_breeding",
                "% Refugia Cells Occupied": "pct_refugia_cells_occupied",
            }
        )

        self.attrs_to_save = attrs_to_save
        self.zarr_group_name = zarr_group_name
        self._zarr_manager = None

    @property
    def zarr_manager(self):

        if self._zarr_manager is None:

            self._zarr_manager = ZarrManager(
                width=self.space.raster_layer.width,
                height=self.space.raster_layer.height,
                max_timestep=self.num_steps,
                crs=self.space.crs,
                transformer_json=self.space.transformer.to_json(),
                run_parameter_dict=TEST_RUN_PARAMETERS,
                attribute_list=self.attrs_to_save,
                filename=ZARR_FILENAME,
            )

            if self.zarr_group_name is None:
                self.zarr_group_name = (
                    self._zarr_manager.set_group_name_by_parameter_hash()
                )
            else:
                self._zarr_manager.set_group_name(self.zarr_group_name)

            self.replicate_idx = self._zarr_manager.resize_array_for_next_replicate()

        return self._zarr_manager

    def _on_start(self):

        self.sim_logger.log_sim_event(self, SimEventType.ON_START)

        self.space.get_elevation()
        self.space.get_aridity()
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
        self.n_breeding = count_dict.get(LifeStage.BREEDING, 0)
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

    def _append_timestep_to_zarr(self):

        timestep_attr_dict = get_array_from_nested_cell_list(
            veg_cells=self.space.raster_layer.cells,
            attr_list=self.attrs_to_save,
        )

        for attr_name in self.attrs_to_save:
            self.zarr_manager.append_synchronized_timestep(
                group_name="test_config_dict_hash",
                attr_name=attr_name,
                replicate_idx=0,
                timestep_idx=self.steps,
                timestep_array=timestep_attr_dict[attr_name],
            )

    def step(self):

        if not self._on_start_executed:
            self._on_start()

        self.sim_logger.log_sim_event(self, SimEventType.ON_STEP)

        self.agents.shuffle_do("step")
        self.update_metrics()

        self.datacollector.collect(self)

        if len(self.attrs_to_save) > 0:
            self._append_timestep_to_zarr()
