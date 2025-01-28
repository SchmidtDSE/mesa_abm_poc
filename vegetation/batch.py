from mesa.batchrunner import batch_run
from vegetation.model.vegetation import Vegetation
from numpy import arange
import os
import argparse
import pandas as pd
from vegetation.config.paths import (
    LOCAL_STAC_CACHE_FSTRING,
    SAVE_LOCAL_STAC_CACHE,
    DEM_STAC_PATH,
)


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
    parser.add_argument("--name", type=str, default=None, help="Simulation name")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing results",
    )
    parsed = parser.parse_args()

    return {
        "interactive": parsed.interactive,
        "run_steps": parsed.steps,
        "run_iterations": parsed.iterations,
        "run_name": parsed.name,
        "overwrite": parsed.overwrite,
    }


# TODO: Implement early stopping when all the JOTR die off
# Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/18

TST_JOTR_BOUNDS = [-116.326332, 33.975823, -116.289768, 34.004147]

model_params = {
    "num_steps": [100],
    "management_planting_density": arange(0, 1, 0.05),
    "export_data": [False],
    "bounds": [TST_JOTR_BOUNDS],
    "attrs_to_save": [["jotr_max_life_stage"]],
}

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
