import xarray as xr
import argparse
import matplotlib.pyplot as plt
import numpy as np
import imageio

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


def create_gif_from_xarray(sim_xarray, output_path, fps=10, cmap="viridis"):
    # Normalize data to 0-255 range (for RGB conversion)
    vmin, vmax = sim_xarray.min(), sim_xarray.max()
    normalized = ((sim_xarray - vmin) * 255 / (vmax - vmin)).astype(np.uint8)

    # Create frames using matplotlib colormap
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

    first_sim = sim_xarray["jotr_max_life_stage"]

    pct_sim_at_least_seed = binary_minimum_by_encoding(first_sim, "Seed")
    pct_sim_at_least_seedling = binary_minimum_by_encoding(first_sim, "Seedling")
    pct_sim_at_least_juvenile = binary_minimum_by_encoding(first_sim, "Juvenile")
    pct_sim_at_least_adult = binary_minimum_by_encoding(first_sim, "Adult")

    create_gif_from_xarray(first_sim, "tst.gif")
