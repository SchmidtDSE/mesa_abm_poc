import cProfile
import pstats
from typing import Tuple
from ipyleaflet.leaflet import GeomanDrawControl

from mesa.visualization import Slider, SolaraViz, make_plot_component
from vegetation.patch.model import Vegetation, JoshuaTreeAgent
from vegetation.patch.space import VegCell
from vegetation.viz.simple_raster_map import make_simple_raster_geospace_component

# from patch.management import init_tree_management_control
from config.stages import LIFE_STAGE_RGB_VIZ_MAP
from config.aoi import TST_JOTR_BOUNDS

# TODO: Push working build to artifact registry, or dockerhub, or something, while
# Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/10
# we wait on mesa-geo PR


model_params = {
    "num_steps": Slider("total number of steps", 20, 1, 100, 1),
    "management_planting_density": Slider(
        "management planting density", 0.1, 0.01, 1.0, 0.01
    ),
    "export_data": False,
    "bounds": TST_JOTR_BOUNDS,
}


def cell_portrayal(agent):

    if isinstance(agent, VegCell):

        # This is very primitive, but essentially we color based on the furthest
        # life stage of any Joshua Tree agent in the cell. If there are no agents,
        # we color based on elevation.

        if agent.jotr_max_life_stage and agent.jotr_max_life_stage > 0:

            rgba = LIFE_STAGE_RGB_VIZ_MAP[agent.jotr_max_life_stage]

        else:
            if not agent.refugia_status:
                debug_normalized_elevation = int((agent.elevation / 5000) * 255)
                rgba = (
                    debug_normalized_elevation,
                    debug_normalized_elevation,
                    debug_normalized_elevation,
                    0.25,
                )
            else:
                rgba = (0, 255, 0, 1)
        return rgba

    if isinstance(agent, JoshuaTreeAgent):

        portrayal = {}
        portrayal["shape"] = "circle"
        portrayal["color"] = "red"
        portrayal["opacity"] = 0.0
        portrayal["fillOpacity"] = 0.0
        portrayal["stroke"] = False
        portrayal["radius"] = 0

        portrayal["description"] = f"Agent ID: {agent.unique_id}"

        return portrayal


model = Vegetation(bounds=TST_JOTR_BOUNDS)

# DEBUG: Running into bounds issue here - going to manually trigger `_on_start` for now to ensure init is the same as before
model._on_start()

tree_management = GeomanDrawControl(drag=False, cut=False, rotate=False, polyline={})
tree_management.on_draw(model.add_agents_from_management_draw)

page = SolaraViz(
    model,
    name="Veg Model",
    components=[
        make_simple_raster_geospace_component(
            cell_portrayal, zoom=14, controls=[tree_management]
        ),
        make_plot_component(
            [
                "Mean Age",
                "N Agents",
                "N Seeds",
                "N Seedlings",
                "N Juveniles",
                "N Adults",
                "N Breeding",
            ],
        ),
        make_plot_component(
            ["% Refugia Cells Occupied"],
        ),
        # make_log_window_component(),
    ],
    model_params=model_params,
)

if __name__ == "__main__":
    # Run your Solara app
    page  # noqa
