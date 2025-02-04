from mesa.batchrunner import batch_run
from vegetation.model.vegetation import Vegetation
import json
import os
import argparse
import pandas as pd
from typing import Optional

CELL_CLASS = "VegCell"


def get_interactive_params() -> dict:
    run_steps = input("Please enter the number of steps you want to simulate: ")

    run_iterations = input(
        "Enter the number of model iterations you want to simulate: "
    )

    run_overwrite = False

    while True:
        run_name = input("Enter the name of your simulation: ")
        output_path = f"vegetation/.local_dev_data/results/{run_name}.csv"

        if os.path.exists(output_path):
            overwrite_prompt = input(
                "That name already exists. Do you want to overwrite? (y/n) "
            )
            if overwrite_prompt.lower() == "y":
                run_overwrite = True
                break
            elif overwrite_prompt.lower() == "n":
                run_overwrite = False
            else:
                print("Invalid input. Please enter 'y' or 'n'")
                continue
        else:
            break

        print(f"Saving results to {output_path}")

    return {
        "interactive": True,
        "run_steps": int(run_steps),
        "run_iterations": int(run_iterations),
        "run_name": run_name,
        "overwrite": run_overwrite,
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
        "--name",
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
        default="vegetation/config/batch_parameters.json",
        help="Path to batch parameters JSON file",
    )
    parser.add_argument(
        "--attribute_encodings_json",
        type=str,
        default="vegetation/config/attribute_encodings.json",
        help="Path to attribute encodings JSON file",
    )
    parser.add_argument(
        "--aoi_bounds_json",
        type=str,
        default="vegetation/config/aoi_bounds.json",
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
        "run_name": parsed.name,
        "overwrite": parsed.overwrite,
        "batch_parameters_json": parsed.batch_parameters_json,
        "attribute_encodings_json": parsed.attribute_encodings_json,
        "aoi_bounds_json": parsed.aoi_bounds_json,
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


if __name__ == "__main__":
    arg_dict = parse_args()

    if arg_dict["interactive"]:
        arg_dict = get_interactive_params()

    if not all(
        [
            arg_dict["attribute_encodings_json"],
            arg_dict["aoi_bounds_json"],
            arg_dict["batch_parameters_json"],
        ]
    ):
        raise ValueError(
            "Either use --interactive, or supply all of --attribute_encodings_json,"
            "--aoi_bounds_json, and --batch_parameters_json"
        )

    output_path = f"vegetation/.local_dev_data/results/{arg_dict['run_name']}.csv"
    if os.path.exists(output_path) and not arg_dict["overwrite"]:
        raise ValueError(
            f"Output path {output_path} exists. Use --overwrite to overwrite"
        )

    run_name = arg_dict["run_name"]

    parameters_dict = construct_model_run_parameters_from_file(
        simulation_name=run_name,
        attribute_encodings_path=arg_dict["attribute_encodings_json"],
        aoi_bounds_path=arg_dict["aoi_bounds_json"],
        batch_parameters_path=arg_dict["batch_parameters_json"],
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

    output_path = (
        os.getenv("MESA_RESULTS_DIR", "/local_dev_data/mesa_results/")
        + f"{run_name}.csv"
    )
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    pd.DataFrame(results).to_csv(output_path)
