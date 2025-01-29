import hashlib
import json
from typing import Any, Dict, List, Optional

import numpy as np
import zarr

from vegetation.space.veg_cell import VegCell


def get_array_from_nested_cell_list(
    veg_cells: List[List[VegCell]], attr_list: List[str]
) -> Dict[str, np.ndarray]:
    def safe_get_attr(cell: VegCell, attr: str) -> int:
        if not hasattr(cell, attr):
            raise AttributeError(f"VegCell object has no attribute '{attr}'")
        value = getattr(cell, attr)
        return -1 if value is None else value

    veg_arrays = {
        attr: np.array(
            [[safe_get_attr(cell, attr) for cell in row] for row in veg_cells]
        )
        for attr in attr_list
    }
    return veg_arrays


class ZarrManager:

    def __init__(
        self,
        width,
        height,
        max_timestep,
        filename,
        attribute_list,
        run_parameter_dict,
        crs=None,
        transformer_json=None,
        group_name=None,
    ):
        self.width, self.height = width, height

        self.max_timestep = max_timestep
        self.filename = filename
        self.crs = crs
        self.transformer_json = transformer_json
        self.attribute_list = attribute_list
        self.run_parameter_dict = run_parameter_dict

        self._initialize_zarr_store(filename)
        self._initialize_synchronizer(filename)
        self._initialize_zarr_root_group()
        self._attr_list = attribute_list

        self._group_name = None

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
        self._zarr_root_group = zarr.open_group(
            store=self._zarr_store, synchronizer=self._synchronizer, path="/"
        )

    def set_group_name(self, group_name: str):
        self._group_name = group_name

    def set_group_name_by_run_parameter_hash(self) -> None:
        self._group_name = self.get_run_parameter_hash(self.run_parameter_dict)

    def _get_or_create_attribute_dataset(self, attribute_name) -> zarr.core.Array:
        if self._group_name not in self._zarr_root_group:
            self._zarr_root_group.create_group(self._group_name)

            self._zarr_root_group[self._group_name].create_dataset(
                attribute_name,
                shape=(
                    0,
                    self.max_timestep,
                    self.width,
                    self.height,
                ),  # 0 replicates
                chunks=(1, self.width, self.height),
                dtype=np.int8,
                extendable=(True, False, False, False),
            )

        attribute_dataset = self._zarr_root_group[self._group_name][attribute_name]
        return attribute_dataset

    def resize_array_for_next_replicate(self) -> int:

        all_next_replicate_idx = []

        for attribute_name in self.attribute_list:
            attribute_dataset = self._get_or_create_attribute_dataset(
                attribute_name=attribute_name
            )

            next_replicate_idx = attribute_dataset.shape[0] + 1
            all_next_replicate_idx.append(next_replicate_idx)

            attribute_dataset.resize(
                next_replicate_idx,
                attribute_dataset.shape[1],
                attribute_dataset.shape[2],
                attribute_dataset.shape[3],
            )

        # Check that all attributes have the same number of replicates -
        # since we will aggregate on replicate_id, this would cause issues
        # since idx X would correspond to different replicates for different attributes
        assert len(np.unique(all_next_replicate_idx)) == 1

        return next_replicate_idx

    def add_to_zarr_root_group(self, name: str):
        if name not in self._zarr_root_group:
            self._zarr_root_group.create_group(name)

    def append_synchronized_timestep(
        self, timestep_idx: int, replicate_idx: int, timestep_array: np.ndarray
    ) -> None:

        sim_array = self._get_or_create_attribute_dataset()
        sim_array[replicate_idx, timestep_idx] = timestep_array
