from mesa.batchrunner import batch_run
from vegetation.model.vegetation import Vegetation
import json
import os
import argparse
import pandas as pd
from typing import Optional


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


def construct_model_run_parameters_from_file(
    simulation_name: str,
    batch_parameters_path: str,
    attribute_encodings_path: Optional[str],
    aoi_bounds_path: Optional[str],
):

    # Read in the configs
    batch_parameters = json.load(open(batch_parameters_path, "r"))

    # Get the model parameters for this particular simulation
    model_run_parameters = batch_parameters[simulation_name]["model_run_params"]
    cell_attributes_to_save = batch_parameters[simulation_name][
        "cell_attributes_to_save"
    ]
    # Replace the string key for bounds with the actual bounds, if provided
    if aoi_bounds_path is not None:
        aoi_bounds = json.load(open(aoi_bounds_path, "r"))
        model_run_parameters["bounds"] = aoi_bounds[model_run_parameters["bounds"]]
    assert "bounds" in model_run_parameters
    assert len(model_run_parameters["bounds"]) == 4
    assert all([isinstance(x, float) for x in model_run_parameters["bounds"]])

    # Include the attribute encodings, for zarr to save within metadata, if provided
    if attribute_encodings_path is not None:
        attribute_encodings = json.load(open(attribute_encodings_path, "r"))
        model_run_parameters["attribute_encodings"] = attribute_encodings

        # TODO: This might be worth enforcing for all simulations (either provided at runtime or in
        # the config file, but since the attrs are within the agent class, it seems like it should be
        # enforced via config)
        assert all(
            [
                attr in model_run_parameters["attribute_encodings"]["cell"].keys()
                for attr in cell_attributes_to_save
            ]
        )
        model_run_parameters["cell_attributes_to_save"] = cell_attributes_to_save

    model_run_parameters["simulation_name"] = simulation_name
    return model_run_parameters


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

    model_run_parameters = construct_model_run_parameters_from_file(
        simulation_name=run_name,
        attribute_encodings_path=arg_dict["attribute_encodings_json"],
        aoi_bounds_path=arg_dict["aoi_bounds_json"],
        batch_parameters_path=arg_dict["batch_parameters_json"],
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
