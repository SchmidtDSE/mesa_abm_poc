import numpy as np
import zarr
from typing import List, Dict, Any
import json
import hashlib
from vegetation.space.veg_cell import VegCell


def get_array_from_nested_cell_list(veg_cells: List[List[VegCell]]) -> np.ndarray:
    def safe_get_stage(cell: VegCell) -> int:
        return -1 if cell.jotr_max_life_stage is None else cell.jotr_max_life_stage

    veg_array = np.array([[safe_get_stage(cell) for cell in row] for row in veg_cells])
    return veg_array


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

    @staticmethod
    def normalize_dict_for_hash(param_dict: Dict[str, Any]) -> Dict[str, Any]:

        def _normalize_value(value: Any) -> Any:
            if isinstance(value, dict):
                return {k: _normalize_value(v) for k, v in sorted(value.items())}
            elif isinstance(value, list):
                return [_normalize_value(v) for v in value]
            elif isinstance(value, str):
                return value.lower()
            return value

        try:
            return _normalize_value(param_dict)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}")

    @staticmethod
    def get_run_parameter_hash(self, run_parameters: Dict[str, Any]) -> str:

        param_str = json.dumps(run_parameters, sort_keys=True)
        param_str_formatted = self.normalize_dict_for_hash(param_str)
        param_hash = hashlib.sha256(param_str_formatted.encode()).hexdigest()
        return param_hash

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

    def append_synchronized_timestep(
        self,
        run_parameters: Dict[str, Any],
        timestep_idx: int,
        replicate_idx: int,
        timestep_array: np.ndarray,
        group_name: Optional[str] = None,
    ) -> None:

        if group_name is None:
            group_name = self.get_run_parameter_hash(run_parameters)

        if group_name not in self._zarr_root_group:

            zarr_group = self._zarr_root_group.create_group(group_name)

            sim_array = zarr_group.create_dataset(
                group_name,
                shape=(0, self.max_timestep, self.x_dim, self.y_dim),  # 0 replicates
                chunks=(1, self.x_dim, self.y_dim),
                dtype=np.int8,
            )

            sim_array.attrs["run_parameters"] = run_parameters

        self._zarr_root_group[group_name][replicate_idx][timestep_idx] = timestep_array
