from mesa.batchrunner import batch_run
from vegetation.patch.model import Vegetation
from numpy import arange
from vegetation.config.paths import (
    LOCAL_STAC_CACHE_FSTRING,
    SAVE_LOCAL_STAC_CACHE,
    DEM_STAC_PATH,
)

# TODO: Implement early stopping when all the JOTR die off
# Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/18

TST_JOTR_BOUNDS = [-116.326332, 33.975823, -116.289768, 34.004147]

model_params = {
    "num_steps": [100],
    "management_planting_density": arange(0, 1, 0.05),
    "export_data": [False],
    "bounds": [TST_JOTR_BOUNDS],
}

if __name__ == "__main__":
    results = batch_run(
        Vegetation,
        parameters=model_params,
        iterations=5,
        max_steps=100,
        number_processes=1,
        data_collection_period=1,
        display_progress=True,
    )
