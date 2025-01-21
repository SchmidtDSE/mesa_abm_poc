import numpy as np
import zarr
from typing import List
from vegetation.patch.space import VegCell


def create_life_stage_zarr(
    veg_cells: List[List[VegCell]], timesteps: int, filename: str
):
    # Get grid dimensions
    n_rows = len(veg_cells)
    n_cols = len(veg_cells[0])

    # Create zarr array
    store = zarr.DirectoryStore(filename)
    life_stages = zarr.create(
        shape=(timesteps, n_rows, n_cols),
        chunks=(1, n_rows, n_cols),  # Chunk by timestep
        dtype=np.int8,  # Assuming small integer values
        store=store,
        fill_value=-1,  # Sentinel value for None
    )

    # Helper to convert None to -1
    def safe_get_stage(cell: VegCell) -> int:
        return -1 if cell.jotr_max_life_stage is None else cell.jotr_max_life_stage

    # For each timestep
    for t in range(timesteps):
        # Convert grid to numpy array for efficient writing
        stage_array = np.array(
            [[safe_get_stage(cell) for cell in row] for row in veg_cells]
        )

        # Write timestep data
        life_stages[t, :, :] = stage_array

    return life_stages


# Usage example:
# life_stages = create_life_stage_zarr(veg_cells, n_timesteps, "life_stages.zarr")
