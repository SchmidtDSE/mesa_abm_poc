from mesa.batchrunner import batch_run
from vegetation.model.vegetation import Vegetation
import json
import os
import argparse
import pandas as pd


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
        "--steps", type=int, default=None, help="Number of simulation steps"
    )
    parser.add_argument(
        "--iterations", type=int, default=None, help="Number of model iterations"
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
        "--save_to_zarr",
        action="store_true",
        default=False,
        help="Save results to Zarr",
    )

    parsed = parser.parse_args()

    return {
        "interactive": parsed.interactive,
        "run_steps": parsed.steps,
        "run_iterations": parsed.iterations,
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
# model_params = {
#     "num_steps": [100],
#     "management_planting_density": arange(0, 1, 0.05),
#     "bounds": [TST_JOTR_BOUNDS],
#     "attrs_to_save": [["jotr_max_life_stage", "test_attribute"]],
#     "attribute_encodings": [
#         {
#             "jotr_max_life_stage": {
#                 "description": "the max life stage of any jotr agent within this VegCell",
#                 "encoding": {
#                     "-1": "No JOTR",
#                     "0": "Seed",
#                     "1": "Seedling",
#                     "2": "Juvenile",
#                     "3": "Adult",
#                     "4": "Breeding",
#                 },
#             },
#             "test_attribute": {
#                 "description": "A meaningless test attribute",
#                 "encoding": {"0": "Test 0", "1": "Test 1", "2": "Test 2"},
#             },
#         }
#     ],
#     # "zarr_group_name": ["initial_test"],
# }


def construct_model_params_from_file(
    simulation_name: str,
    attribute_encodings_path: str,
    aoi_bounds_path: str,
    batch_parameters_path: str,
):

    attribute_encodings = json.load(open(attribute_encodings_path, "r"))
    aoi_bounds = json.load(open(aoi_bounds_path, "r"))
    batch_parameters = json.load(open(batch_parameters_path, "r"))

    aoi_bounds = batch_parameters["model_run_params"]["bounds"]
    batch_parameters = batch_parameters[simulation_name]

    model_params = {}
    model_params = model_params.extend(aoi_bounds)
    model_params = model_params.extend(attribute_encodings)
    model_params["bounds"] = aoi_bounds
    model_params["zarr_group_name"] = simulation_name

    return model_params


if __name__ == "__main__":
    arg_dict = parse_args()

    if arg_dict["interactive"]:
        arg_dict = get_interactive_params()

    if not all(
        [arg_dict["run_steps"], arg_dict["run_iterations"], arg_dict["run_name"]]
    ):
        raise ValueError(
            "Either use --interactive, or in non-interactive mode, --steps, --iterations, and --name are required"
        )

    output_path = f"vegetation/.local_dev_data/results/{arg_dict['run_name']}.csv"
    if os.path.exists(output_path) and not arg_dict["overwrite"]:
        raise ValueError(
            f"Output path {output_path} exists. Use --overwrite to overwrite"
        )

    run_steps = arg_dict["run_steps"]
    run_iterations = arg_dict["run_iterations"]
    run_name = arg_dict["run_name"]

    model_params = construct_model_params_from_file(
        arg_dict["attribute_encodings_json"],
        arg_dict["aoi_bounds_json"],
        arg_dict["batch_parameters_json"],
    )

    results = batch_run(
        Vegetation,
        parameters=model_params,
        iterations=run_iterations,
        max_steps=run_steps,
        number_processes=1,
        data_collection_period=1,
        display_progress=True,
    )

    output_path = f"vegetation/.local_dev_data/results/{run_name}.csv"
    pd.DataFrame(results).to_csv(output_path)
