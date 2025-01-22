import numpy as np
import zarr
from typing import List, Tuple, Optional
from vegetation.patch.space import VegCell


def initialize_synchronized_zarr(grid_shape, filename, crs=None, transformer_json=None):
    """Initialize a thread-safe Zarr array for multiple parallel simulations"""

    store = zarr.DirectoryStore(filename)
    sync_store = zarr.ProcessSynchronizer(filename + ".sync")

    return zarr.create(
        shape=(0, 0, grid_shape[0], grid_shape[1]),  # (sim_id, time, x, y)
        chunks=(1, 1, grid_shape[0], grid_shape[1]),
        dtype=np.int8,
        store=store,
        synchronizer=sync_store,
        extendable=(True, True, False, False),  # allow extending sim_id and time
    )


def append_synchronized_timestep(
    zarr_array: zarr.Array, sim_idx: int, timestep_idx: int, timestep_array: np.ndarray
) -> None:
    """Thread-safe append of simulation timestep"""

    if sim_idx >= zarr_array.shape[0]:
        zarr_array.resize(sim_idx + 1, axis=0)
    if zarr_array.shape[1] <= timestep_idx:
        zarr_array.resize(timestep_idx + 1, axis=1)

    zarr_array[sim_idx, timestep_idx] = timestep_array


def get_array_from_nested_cell_list(veg_cells: List[List[VegCell]]) -> np.ndarray:
    """Get a numpy array from a list of lists of VegCell objects"""

    def safe_get_stage(cell: VegCell) -> int:
        return -1 if cell.jotr_max_life_stage is None else cell.jotr_max_life_stage

    veg_array = np.array([[safe_get_stage(cell) for cell in row] for row in veg_cells])
    return veg_array
