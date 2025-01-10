import xyzservices
import ipyleaflet
import solara
from mesa.visualization.utils import update_counter
from mesa_geo.visualization.components.geospace_component import MapModule


def make_simple_raster_geospace_component(
    agent_portrayal,
    view=None,
    tiles=xyzservices.providers.OpenStreetMap.Mapnik,
    **kwargs,
):
    def MakeSpaceMatplotlib(model):
        return RasterOnlyGeoSpaceLeaflet(model, agent_portrayal, view, tiles, **kwargs)

    return MakeSpaceMatplotlib


class RasterOnlyMapModule(MapModule):
    """
    Subclassing MapModule so we don't render agents at all, just the raster layers
    (which have aggregated agent info already)
    """

    def render(self, model):
        return {
            "layers": self._render_layers(model),
            "agents": [
                {"type": "FeatureCollection", "features": []},
                [],
            ],
        }


@solara.component
def RasterOnlyGeoSpaceLeaflet(model, agent_portrayal, view, tiles, **kwargs):
    """
    A simple raster map visualization component for Solara, which borrows heavily
    (is a reduced version of) `mesa-geo`'s MapModule. This is created to just ignore
    the agent render and show just the raster layers, where the aggregation makes
    the visualization run much faster.
    """
    update_counter.get()
    map_drawer = RasterOnlyMapModule(portrayal_method=agent_portrayal, tiles=tiles)
    model_view = map_drawer.render(model)

    if view is None:
        # longlat [min_x, min_y, max_x, max_y] to latlong [min_y, min_x, max_y, max_x]
        transformed_xx, transformed_yy = model.space.transformer.transform(
            xx=[model.space.total_bounds[0], model.space.total_bounds[2]],
            yy=[model.space.total_bounds[1], model.space.total_bounds[3]],
        )
        view = [
            (transformed_yy[0] + transformed_yy[1]) / 2,
            (transformed_xx[0] + transformed_xx[1]) / 2,
        ]

    layers = (
        [ipyleaflet.TileLayer.element(url=map_drawer.tiles["url"])] if tiles else []
    )
    for layer in model_view["layers"]["rasters"]:
        layers.append(
            ipyleaflet.ImageOverlay(
                url=layer["url"],
                bounds=layer["bounds"],
            )
        )
    for layer in model_view["layers"]["vectors"]:
        layers.append(ipyleaflet.GeoJSON(element=layer))
    ipyleaflet.Map.element(
        center=view,
        layers=[
            *layers,
            ipyleaflet.GeoJSON.element(data=model_view["agents"][0]),
            *model_view["agents"][1],
        ],
        **kwargs,
    )
