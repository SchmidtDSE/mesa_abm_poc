import xarray as xr
import argparse
import matplotlib.pyplot as plt
import numpy as np
import imageio
from io import BytesIO

ZARR_PATH = "vegetation.zarr"

sim_xarray = xr.open_zarr(ZARR_PATH)


def ingest_zarr(zarr_path, group_name=None):
    try:
        sim_xarray = xr.open_zarr(
            store=zarr_path,
            group=group_name,
            consolidated=True,
            chunks="auto",
        )
        return sim_xarray

    except (OSError, ValueError) as e:
        print(f"Error opening Zarr dataset: {e}")


def create_gif_from_xarray(
    aggregated_dict, output_path, fps=10, cmap="viridis", vmin=None, vmax=None
):
    sim_xarray = aggregated_dict["aggregated_xarray"]

    if vmin is None:
        vmin = sim_xarray.min().values
    if vmax is None:
        vmax = sim_xarray.max().values

    normalized = ((sim_xarray - vmin) * 255 / (vmax - vmin)).astype(np.uint8)

    frames = []
    for timestep_idx in sim_xarray.timestep:
        # Convert to RGB using colormap
        frame = plt.get_cmap(cmap)(normalized[timestep_idx].values)
        # Convert to 0-255 uint8
        frame = (frame * 255).astype(np.uint8)
        frames.append(frame)

    # Save as GIF
    imageio.mimsave(output_path, frames, fps=fps)


def binary_minimum_by_encoding(attribute_xarray, attribute_minimum_key):
    attribute_encoding = attribute_xarray.attribute_encoding

    description = attribute_encoding.get("description", None)
    attribute_encoding = attribute_encoding.get("encoding", None)

    if attribute_encoding is None:
        raise ValueError(
            "Target attribute does not have an encoding, so it cannot be aggregated."
        )

    if attribute_minimum_key not in attribute_encoding:
        raise ValueError(
            f"Minimum key {attribute_minimum_key} not found in attribute encoding."
        )

    min_threshold = attribute_encoding[attribute_minimum_key]
    binary_result = (attribute_xarray >= min_threshold).astype(float)
    result = binary_result.mean(dim="replicate_id")

    result = {
        "aggregated_xarray": result,
        "description": description,
        "aggregation": f"Percent of simulations with at least {attribute_minimum_key}",
    }

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Zarr data")
    parser.add_argument(
        "--zarr_path",
        type=str,
        default=ZARR_PATH,
        help="Path to Zarr data",
    )
    parser.add_argument(
        "--group_name",
        type=str,
        default=None,
        help="Name of simulation group name",
    )
    args = parser.parse_args()
    sim_xarray = ingest_zarr(zarr_path=args.zarr_path, group_name=args.group_name)

    jotr_max_life_stage_xarray = sim_xarray["jotr_max_life_stage"]

    print(
        f"Aggregating {jotr_max_life_stage_xarray.name} (n = {sim_xarray.dims['replicate_id']})..."
    )

    pct_sim_at_least_seed = binary_minimum_by_encoding(
        jotr_max_life_stage_xarray,
        "SEED",
    )
    pct_sim_at_least_seedling = binary_minimum_by_encoding(
        jotr_max_life_stage_xarray,
        "SEEDLING",
    )
    pct_sim_at_least_juvenile = binary_minimum_by_encoding(
        jotr_max_life_stage_xarray,
        "JUVENILE",
    )
    pct_sim_at_least_adult = binary_minimum_by_encoding(
        jotr_max_life_stage_xarray,
        "ADULT",
    )

    create_gif_from_xarray(
        pct_sim_at_least_seed, "pct_at_least_seed.gif", vmin=0, vmax=1
    )
    create_gif_from_xarray(
        pct_sim_at_least_seedling, "pct_at_least_seedling.gif", vmin=0, vmax=1
    )
    create_gif_from_xarray(
        pct_sim_at_least_juvenile, "pct_at_least_juvenile.gif", vmin=0, vmax=1
    )
    create_gif_from_xarray(
        pct_sim_at_least_adult, "pct_at_least_adult.gif", vmin=0, vmax=1
    )
