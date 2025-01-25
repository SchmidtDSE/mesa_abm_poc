import numpy as np
import zarr
from typing import List, Dict, Any
import json
import hashlib
from vegetation.space.veg_cell import VegCell


class ZarrManager:
    def __init__(
        self, grid_shape, max_timestep, filename, crs=None, transformer_json=None
    ):
        self.grid_shape = grid_shape
        self.x_dim, self.y_dim = grid_shape

        self.max_timestep = max_timestep
        self.filename = filename
        self.crs = crs
        self.transformer_json = transformer_json

        self._initialize_zarr_store(filename)
        self._initialize_synchronizer(filename)
        self._initialize_zarr_root_group()

    def _initialize_zarr_store(self, filename):
        self._zarr_store = zarr.DirectoryStore(filename)

    def _initialize_synchronizer(self, filename):
        self._synchronizer = zarr.ProcessSynchronizer(filename + ".sync")

    def _initialize_zarr_root_group(self):
        self._zarr_root_group = zarr.group(
            store=self.zarr_store, synchronizer=self._synchronizer
        )

    def initialize_zarr_group(
        filename: str,
    ) -> zarr.Group:
        store = zarr.DirectoryStore(filename)
        sync_store = zarr.ProcessSynchronizer(filename + ".sync")

        return zarr.group(store=store, synchronizer=sync_store)

    def get_run_parameter_hash(run_parameters: Dict[str, Any]) -> str:
        param_str = json.dumps(run_parameters, sort_keys=True)
        return hashlib.sha256(param_str.encode()).hexdigest()

    def append_synchronized_timestep(
        self,
        run_parameters: Dict[str, Any],
        timestep_idx: int,
        replicate_idx: int,
        timestep_array: np.ndarray,
    ) -> None:
        param_hash = self.get_run_parameter_hash(run_parameters)

        if param_hash not in self._zarr_root_group:

            param_hash_group = self._zarr_root_group.create_group(param_hash)

            sim_array = param_hash_group.create_dataset(
                param_hash,
                shape=(0, self.max_timestep, self.x_dim, self.y_dim),  # 0 replicates
                chunks=(1, self.x_dim, self.y_dim),
                dtype=np.int8,
            )

            sim_array.attrs["run_parameters"] = run_parameters

        self._zarr_root_group[param_hash][replicate_idx][timestep_idx] = timestep_array

    def get_array_from_nested_cell_list(veg_cells: List[List[VegCell]]) -> np.ndarray:
        def safe_get_stage(cell: VegCell) -> int:
            return -1 if cell.jotr_max_life_stage is None else cell.jotr_max_life_stage

        veg_array = np.array(
            [[safe_get_stage(cell) for cell in row] for row in veg_cells]
        )
        return veg_array
