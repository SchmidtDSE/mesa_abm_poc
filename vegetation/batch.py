import argparse
import os

import pandas as pd
from mesa.batchrunner import batch_run
from numpy import arange

from vegetation.patch.model import Vegetation


def get_interactive_params() -> dict:
    run_steps = input("Please enter the number of steps you want to simulate: ")
    print(f"Simulating {run_steps} steps")

    run_iter = input("Enter the number of model iterations you want to simulate: ")
    print(f"Simulating {run_iter} iterations")

    while True:
        run_name = input("Enter the name of your simulation: ")
        output_path = f"vegetation/.local_dev_data/results/{run_name}"
        print(f"Saving results to {output_path}")

        if os.path.exists(output_path):
            overwrite = input(
                "That name already exists. Do you want to overwrite? (y/n) "
            )
            if overwrite.lower() == "y":
                break
            elif overwrite.lower() == "n":
                continue
        else:
            break

    return {
        "run_steps": int(run_steps),
        "run_iter": int(run_iter),
        "run_name": run_name,
    }


def parse_args() -> dict:
    parser = argparse.ArgumentParser(description="Run vegetation simulation")
    parser.add_argument(
        "--interactive", action="store_true", help="Run in interactive mode"
    )
    parser.add_argument("--steps", type=int, help="Number of simulation steps")
    parser.add_argument("--iterations", type=int, help="Number of model iterations")
    parser.add_argument("--name", type=str, help="Simulation name")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing results",
    )
    parsed = parser.parse_args()

    return {
        "interactive": parsed.interactive,
        "steps": parsed.steps,
        "iterations": parsed.iterations,
        "name": parsed.name,
        "overwrite": parsed.overwrite,
    }


TST_JOTR_BOUNDS = [-116.326332, 33.975823, -116.289768, 34.004147]

model_params = {
    "num_steps": [3],
    "management_planting_density": arange(0, 1, 0.05),
    "export_data": [False],
    "bounds": [TST_JOTR_BOUNDS],
}

if __name__ == "__main__":
    args = parse_args()

    if args["interactive"]:
        run_steps, run_iterations, run_name = get_interactive_params()
    else:
        if not all([args["steps"], args["iterations"], args["name"]]):
            raise ValueError(
                "In non-interactive mode, --steps, --iterations, and --name are required"
            )

        output_path = f"vegetation/.local_dev_data/results/{args['name']}"
        if os.path.exists(output_path) and not args["overwrite"]:
            raise ValueError(
                f"Output path {output_path} exists. Use --force to overwrite"
            )

        run_steps = args["steps"]
        run_iterations = args["iterations"]
        run_name = args["name"]

    results = batch_run(
        Vegetation,
        parameters=model_params,
        iterations=run_iterations,
        max_steps=run_steps,
        number_processes=1,
        data_collection_period=1,
        display_progress=True,
    )

    output_path = f"vegetation/.local_dev_data/results/{run_name}"
    pd.DataFrame(results).to_csv(output_path)
