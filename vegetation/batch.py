from mesa.batchrunner import batch_run
from vegetation.model.vegetation import Vegetation
import json
import os
import argparse
import pandas as pd
from typing import Optional

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


def get_interactive_params(
    batch_parameters_path: Optional[str] = DEFAULT_BATCH_PARAMETERS_PATH,
    attribute_encodings_path: Optional[str] = DEFAULT_ATTRIBUTE_ENCODINGS_PATH,
    aoi_bounds_path: Optional[str] = DEFAULT_AOI_BOUNDS_PATH,
) -> dict:
    # Load configs first
    batch_parameters = json.load(open(batch_parameters_path, "r"))
    simulation_parameters = None

    # Let user select simulation or enter new name
    print("\nAvailable simulations (or enter new name):")
    for idx, sim in enumerate(batch_parameters.keys()):
        if sim != "__interactive_default":
            print(f"{idx}: {sim}")

    while True:
        selection = input("\nSelect simulation number or enter new name: ")
        try:
            # Try numeric selection first
            sim_idx = int(selection)
            simulation_name = list(
                k for k in batch_parameters.keys() if k != "__interactive_default"
            )[sim_idx]
            simulation_parameters = batch_parameters[simulation_name]
            break
        except ValueError:
            # If not numeric, treat as new simulation name
            simulation_name = selection
            if "__interactive_default" not in batch_parameters:
                print("Error: __interactive_default template not found in parameters")
                exit(1)
            simulation_parameters = batch_parameters["__interactive_default"].copy()
            break
        except IndexError:
            print("Invalid selection. Try again.")

    output_path = (
        os.getenv("MESA_RESULTS_DIR", "/local_dev_data/mesa_results/")
        + f"{simulation_name}.csv"
    )
    if os.path.exists(output_path):
        print(f"Output path {output_path} exists.")
        overwrite = input("Overwrite? [y/n]: ")
        if overwrite.lower() != "y":
            print("Exiting.")
            exit()

    if not simulation_parameters:
        simulation_parameters = batch_parameters[simulation_name]
    meta_parameters = simulation_parameters["meta_parameters"]
    model_run_parameters = simulation_parameters["model_run_params"]
    cell_attributes_to_save = simulation_parameters["cell_attributes_to_save"]

    # Interactive override of meta parameters
    print("\nMeta parameters (press Enter to keep default):")
    for key, value in meta_parameters.items():
        user_input = input(f"{key} [{value}]: ")
        if user_input.strip():
            meta_parameters[key] = type(value)(user_input)

    # Interactive override of model parameters
    print("\nModel parameters (press Enter to keep default):")
    for key, value in model_run_parameters.items():
        user_input = input(f"{key} [{value}]: ")
        if user_input.strip():
            model_run_parameters[key] = type(value)(user_input)

    # Handle bounds
    aoi_bounds = None
    if aoi_bounds_path:
        aoi_bounds_options = json.load(open(aoi_bounds_path, "r"))
        print("\nAvailable bounds:")
        for idx, (key, bounds) in enumerate(aoi_bounds_options.items()):
            print(f"{idx}: {key} {bounds}")
        while True:
            try:
                bounds_idx = int(input("\nSelect bounds number: "))
                aoi_bounds = list(aoi_bounds_options.values())[bounds_idx]
                break
            except (ValueError, IndexError):
                print("Invalid selection. Try again.")

    # Handle attribute encodings
    attribute_encodings = None
    if attribute_encodings_path:
        attribute_encodings = json.load(open(attribute_encodings_path, "r"))
        attribute_encodings = attribute_encodings[CELL_CLASS]

    model_run_parameters["simulation_name"] = simulation_name

    return {
        "meta_parameters": meta_parameters,
        "model_run_parameters": model_run_parameters,
        "attribute_encodings": attribute_encodings,
        "aoi_bounds": aoi_bounds,
        "cell_attributes_to_save": cell_attributes_to_save,
    }


# TODO: Implement early stopping when all the JOTR die off
# Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/18

# TODO: Figure out how model_params is passed to mesa
# Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/38
# This is causing issues regarding how many sims are actually run


def construct_model_run_parameters_from_file(
    simulation_name: str,
    batch_parameters_path: str,
    attribute_encodings_path: Optional[str],
    aoi_bounds_path: Optional[str],
):
    # Read in the configs
    batch_parameters = json.load(open(batch_parameters_path, "r"))
    simulation_parameters = batch_parameters[simulation_name]
    # Get meta parameters for this batch run (things not relevant to specific model runs)
    meta_parameters = simulation_parameters["meta_parameters"]

    # Get the model parameters for this particular simulation
    model_run_parameters = simulation_parameters["model_run_params"]

    # Get the cell-level attributes to save to zarr
    cell_attributes_to_save = simulation_parameters["cell_attributes_to_save"]

    # Replace the string key for bounds with the actual bounds, if provided
    if aoi_bounds_path is not None:
        aoi_bounds_options = json.load(open(aoi_bounds_path, "r"))
        aoi_bounds_key = simulation_parameters["bounds_key"]
        aoi_bounds = aoi_bounds_options[aoi_bounds_key]
        del simulation_parameters["bounds_key"]

    assert len(aoi_bounds) == 4
    assert all([isinstance(x, float) for x in aoi_bounds])

    # Include the attribute encodings, for zarr to save within metadata, if provided
    if attribute_encodings_path is not None:
        attribute_encodings = json.load(open(attribute_encodings_path, "r"))
        attribute_encodings = attribute_encodings[CELL_CLASS]

        # TODO: This might be worth enforcing for all simulations
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/39
        #  (either provided at runtime or in  the config file, but since
        # the attrs are within the agent class, it seems like it in config)
        if cell_attributes_to_save is not None:
            assert all(
                [attr in attribute_encodings.keys() for attr in cell_attributes_to_save]
            )

    model_run_parameters["simulation_name"] = simulation_name

    return {
        "meta_parameters": meta_parameters,
        "model_run_parameters": model_run_parameters,
        "attribute_encodings": attribute_encodings,
        "aoi_bounds": aoi_bounds,
        "cell_attributes_to_save": cell_attributes_to_save,
    }


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

    else:
        simulation_name = arg_dict["run_name"]

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

    if os.path.exists(output_path) and not arg_dict["overwrite"]:
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

    results = batch_run(
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
