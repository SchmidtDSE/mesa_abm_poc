from mesa.batchrunner import batch_run
from vegetation.model.vegetation import Vegetation
import os
import argparse
import pandas as pd

from vegetation.batch.routes import (
    get_interactive_params,
    construct_model_run_parameters_from_file,
)
from vegetation.batch.batchrunner import batch_run_serialized

CELL_CLASS = "VegCell"
DEFAULT_BATCH_PARAMETERS_PATH = os.getenv(
    "DEFAULT_BATCH_PARAMETERS_PATH", "vegetation/config/batch_parameters.json"
)
DEFAULT_ATTRIBUTE_ENCODINGS_PATH = os.getenv(
    "DEFAULT_ATTRIBUTE_ENCODINGS_PATH", "vegetation/config/attribute_encodings.json"
)
DEFAULT_AOI_BOUNDS_PATH = os.getenv(
    "DEFAULT_AOI_BOUNDS_PATH", "vegetation/config/aoi_bounds.json"
)


def parse_args() -> dict:
    parser = argparse.ArgumentParser(description="Run vegetation simulation")
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=None,
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--simulation_name",
        type=str,
        default=None,
        help="Simulation name (used as the Zarr group name)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing results",
    )
    parser.add_argument(
        "--batch_parameters_json",
        type=str,
        default=DEFAULT_BATCH_PARAMETERS_PATH,
        help="Path to batch parameters JSON file",
    )
    parser.add_argument(
        "--attribute_encodings_json",
        type=str,
        default=DEFAULT_ATTRIBUTE_ENCODINGS_PATH,
        help="Path to attribute encodings JSON file",
    )
    parser.add_argument(
        "--aoi_bounds_json",
        type=str,
        default=DEFAULT_AOI_BOUNDS_PATH,
        help="Path to AOI bounds JSON file",
    )
    parser.add_argument(
        "--zarr_store",
        type=str,
        default="directory",
        help="Type of Zarr store for saving artifacts ('directory' or 'gcp')",
    )

    parsed = parser.parse_args()

    return {
        "interactive": parsed.interactive,
        "simulation_name": parsed.simulation_name,
        "overwrite": parsed.overwrite,
        "batch_parameters_json": parsed.batch_parameters_json,
        "attribute_encodings_json": parsed.attribute_encodings_json,
        "aoi_bounds_json": parsed.aoi_bounds_json,
    }


if __name__ == "__main__":
    arg_dict = parse_args()

    if (
        not all(
            [
                arg_dict["attribute_encodings_json"],
                arg_dict["aoi_bounds_json"],
                arg_dict["batch_parameters_json"],
            ]
        )
        or not arg_dict["interactive"]
    ):
        raise ValueError(
            "Either use --interactive, or supply all of --attribute_encodings_json,"
            "--aoi_bounds_json, and --batch_parameters_json"
        )

    if arg_dict["interactive"]:
        parameters_dict = get_interactive_params()
        simulation_name = parameters_dict["model_run_parameters"]["simulation_name"]
        overwrite = parameters_dict["overwrite"]

    else:
        simulation_name = arg_dict["run_name"]
        overwrite = arg_dict["overwrite"]
        parameters_dict = construct_model_run_parameters_from_file(
            simulation_name=simulation_name,
            attribute_encodings_path=arg_dict["attribute_encodings_json"],
            aoi_bounds_path=arg_dict["aoi_bounds_json"],
            batch_parameters_path=arg_dict["batch_parameters_json"],
        )

    output_path = (
        os.getenv("MESA_RESULTS_DIR", "/local_dev_data/mesa_results/")
        + f"{simulation_name}.csv"
    )

    if os.path.exists(output_path) and not overwrite:
        raise ValueError(
            f"Output path {output_path} exists. Use --overwrite to overwrite"
        )

    model_run_parameters = parameters_dict["model_run_parameters"]
    meta_parameters = parameters_dict["meta_parameters"]
    attribute_encodings = parameters_dict["attribute_encodings"]
    aoi_bounds = parameters_dict["aoi_bounds"]
    cell_attributes_to_save = parameters_dict["cell_attributes_to_save"]

    Vegetation.set_attribute_encodings(attribute_encodings=attribute_encodings)
    Vegetation.set_aoi_bounds(aoi_bounds=aoi_bounds)
    Vegetation.set_cell_attributes_to_save(
        cell_attributes_to_save=cell_attributes_to_save
    )

    results = batch_run_serialized(
        Vegetation,
        parameters=model_run_parameters,
        iterations=meta_parameters["num_iterations_per_worker"],
        number_processes=meta_parameters["num_workers"],
        data_collection_period=1,
        display_progress=True,
    )

    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    pd.DataFrame(results).to_csv(output_path)
