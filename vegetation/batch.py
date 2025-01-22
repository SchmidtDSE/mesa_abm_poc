from mesa.batchrunner import batch_run
from vegetation.patch.model import Vegetation
from numpy import arange
from vegetation.config.paths import (
    LOCAL_STAC_CACHE_FSTRING,
    SAVE_LOCAL_STAC_CACHE,
    DEM_STAC_PATH,
)

import pandas as pd
import os as os

run_steps = input("Setting up a simulation. Please enter the number of steps you want to simulate: ")
print(f'Simulating {run_steps} steps')

run_iter = input("Enter the number of model iterations you want to simulate: ")
print(f'Simulating {run_iter} iterations')

run_name = ""
while True:
    run_name = input("Enter the name of your simulation: ")
    print(f'Saving results to vegetation/.local_dev_data/results/{run_name}.')

    if os.path.exists(f'vegetation/.local_dev_data/results/{run_name}'):
        overwrite = input("That name already exists. Do you want to overwrite? (y/n) ")
        if overwrite == 'n':
            continue 
        elif overwrite == 'y':
            break 
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
    else:
        break 





# TODO: Implement early stopping when all the JOTR die off
# Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/18

TST_JOTR_BOUNDS = [-116.326332, 33.975823, -116.289768, 34.004147]

model_params = {
    "num_steps": [3],
    "management_planting_density": arange(0, 1, 0.05),
    "export_data": [False],
    "bounds": [TST_JOTR_BOUNDS],
}

if __name__ == "__main__":
    results = batch_run(
        Vegetation,
        parameters=model_params,
        iterations=int(run_iter),
        max_steps=int(run_steps),
        number_processes=1,
        data_collection_period=1,
        display_progress=True,
    )

    pd.DataFrame(results).to_csv(f'vegetation/.local_dev_data/results/{run_name}')
