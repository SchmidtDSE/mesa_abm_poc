import hashlib
import json
import os
from typing import Any, Dict, List

import numpy as np
import zarr
from zarr.storage import FSStore

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
        attribute_encodings,
        run_parameter_dict,
        crs=None,
        transformer_json=None,
        zarr_store_type="gcp",
    ):
        self.width, self.height = width, height

        self.max_timestep = max_timestep
        self.filename = filename
        self.crs = crs
        self.transformer_json = transformer_json
        self.attribute_list = attribute_list
        self.attribute_encodings = attribute_encodings

        self.run_parameter_dict = self.normalize_dict_for_hash(run_parameter_dict)
        self._attr_list = attribute_list

        self._group_name = None
        self._replicate_idx = None

        self._initialize_zarr_store(filename, type=zarr_store_type)
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
                stripped_value = value.strip()  # remove leading/trailing whitespace
                return stripped_value.lower()  # normalize to lowercase
            return value

        try:
            return _normalize_value(param_dict)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}")

    def _get_run_parameter_hash(self) -> str:
        run_parameter_str = json.dumps(self.run_parameter_dict, sort_keys=True)
        param_hash = hashlib.sha256(run_parameter_str.encode()).hexdigest()
        return param_hash

    def _initialize_zarr_store(self, filename, type="directory"):
        if type == "directory":

            self._zarr_store = zarr.DirectoryStore(filename)

        elif type == "gcp":

            import gcsfs

            GCP_APPLICATION_DEFAULT_CREDENTIALS_PATH = os.getenv(
                "GCP_APPLICATION_DEFAULT_CREDENTIALS_PATH",
                "~/.config/gcloud/application_default_credentials.json",
            )
            fs = gcsfs.GCSFileSystem(
                token=GCP_APPLICATION_DEFAULT_CREDENTIALS_PATH,
            )

            self._zarr_store = FSStore(
                "gs://dse-nps-mesa/mesa_jotr_poc/" + filename,
                fs=fs,
            )
        else:
            raise ValueError(f"Invalid store type: {type}")

    def _initialize_synchronizer(self, filename):
        self._synchronizer = zarr.ProcessSynchronizer(filename + ".sync")

    def _initialize_zarr_root_group(self):
        self._zarr_root_group = zarr.open_group(
            store=self._zarr_store, synchronizer=self._synchronizer, path="/"
        )

    def set_group_name(self, group_name: str):
        self._group_name = group_name

    def set_group_name_by_run_parameter_hash(self) -> None:
        self._group_name = self._get_run_parameter_hash()

    def _get_or_create_sim_group(self) -> zarr.hierarchy.Group:
        if self._group_name not in self._zarr_root_group:
            sim_group = self._zarr_root_group.create_group(self._group_name)
        else:
            sim_group = self._zarr_root_group[self._group_name]

        sim_group.attrs["run_parameters"] = self.run_parameter_dict
        return sim_group

    def _get_or_create_attribute_dataset(self, attribute_name: str) -> zarr.core.Array:

        sim_group = self._get_or_create_sim_group()

        if attribute_name not in sim_group:
            self._initialize_attribute_dataset(attribute_name=attribute_name)

        attribute_dataset = self._zarr_root_group[self._group_name][attribute_name]
        return attribute_dataset

    def _initialize_attribute_dataset(self, attribute_name: str) -> None:

        attribute_encoding = self.attribute_encodings[attribute_name]

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

        # Xarray needs to know the dimensions of the array, so we store them as
        # `_ARRAY_DIMENSIONS` attribute - see https://docs.xarray.dev/en/latest/internals/zarr-encoding-spec.html
        self._zarr_root_group[self._group_name][attribute_name].attrs[
            "_ARRAY_DIMENSIONS"
        ] = ["replicate_id", "timestep", "x", "y"]

        self._zarr_root_group[self._group_name][attribute_name].attrs[
            "attribute_encoding"
        ] = attribute_encoding

    def resize_array_for_next_replicate(self) -> int:

        all_next_replicate_idx = []

        for attribute_name in self.attribute_list:
            attribute_dataset = self._get_or_create_attribute_dataset(
                attribute_name=attribute_name
            )

            # The next replicate index is the current shape of the dataset - this is
            # a fencepost issue, since the replicate number is 0-indexed but we need to have
            # a dim of the replicate number + 1 to have a space for the next replicate
            next_replicate_idx = attribute_dataset.shape[0]
            all_next_replicate_idx.append(next_replicate_idx)

            attribute_dataset.resize(
                next_replicate_idx + 1,  # +1 for the next replicate
                attribute_dataset.shape[1],
                attribute_dataset.shape[2],
                attribute_dataset.shape[3],
            )

        # Check that all attributes have the same number of replicates -
        # since we will aggregate on replicate_id, this would cause issues
        # since idx X would correspond to different replicates for different attributes
        replicate_idx = np.unique(all_next_replicate_idx)
        assert len(replicate_idx) == 1

        self.replicate_idx = replicate_idx[0]
        return self.replicate_idx

    def add_to_zarr_root_group(self, name: str):
        if name not in self._zarr_root_group:
            self._zarr_root_group.create_group(name)

    def append_synchronized_timestep(
        self, timestep_idx: int, timestep_array_dict: Dict[str, np.ndarray]
    ) -> None:

        for attribute_name, timestep_array in timestep_array_dict.items():
            sim_array = self._get_or_create_attribute_dataset(attribute_name)
            sim_array[self.replicate_idx, timestep_idx] = timestep_array

        self.consolidate_metadata()

    def consolidate_metadata(self):
        zarr.consolidate_metadata(self._zarr_store)
