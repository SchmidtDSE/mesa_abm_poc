from vegetation.batch import batch_run, construct_model_run_parameters_from_file
from vegetation.model.vegetation import Vegetation
import pandas as pd
import os
import pathlib


def test_batch_run_basic():
    # Set up minimal test parameters

    test_configs_dir = os.getenv(
        "TEST_CONFIGS_DIR", "/workspaces/mesa_abm_poc/tests/assets/configs"
    )
    test_configs_dir = pathlib.Path(test_configs_dir)

    parameters_dict = construct_model_run_parameters_from_file(
        "pytest",
        batch_parameters_path=test_configs_dir.joinpath("test_batch_parameters.json"),
        attribute_encodings_path=test_configs_dir.joinpath(
            "test_attribute_encodings.json"
        ),
        aoi_bounds_path=test_configs_dir.joinpath("test_aoi_bounds.json"),
    )

    model_run_parameters = parameters_dict["model_run_parameters"]
    meta_parameters = parameters_dict["meta_parameters"]

    # Run simulation with minimal parameters
    results = batch_run(
        Vegetation,
        parameters=model_run_parameters,
        iterations=meta_parameters["num_iterations_per_worker"],
        number_processes=meta_parameters["num_workers"],
        data_collection_period=1,
        display_progress=False,
    )

    results_pd = pd.DataFrame(results)

    # Basic validation
    assert isinstance(results_pd, pd.DataFrame)
    assert len(results) > 0

    # Check expected columns exist
    expected_columns = {"RunId", "iteration", "Step"}
    assert all(col in results_pd.columns for col in expected_columns)
