from vegetation.batch.run import (
    jotr_batch_run,
    construct_model_run_parameters_from_file,
)
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
    attribute_encodings = parameters_dict["attribute_encodings"]
    aoi_bounds = parameters_dict["aoi_bounds"]
    cell_attributes_to_save = parameters_dict["cell_attributes_to_save"]

    # Vegetation.set_attribute_encodings(attribute_encodings=attribute_encodings)
    # Vegetation.set_aoi_bounds(aoi_bounds=aoi_bounds)
    # Vegetation.set_cell_attributes_to_save(
    #     cell_attributes_to_save=cell_attributes_to_save
    # )

    class_parameters_dict = {
        "attribute_encodings": attribute_encodings,
        "aoi_bounds": aoi_bounds,
        "cell_attributes_to_save": cell_attributes_to_save,
    }

    # Run simulation with minimal parameters
    results = jotr_batch_run(
        Vegetation,
        model_parameters=model_run_parameters,
        class_parameters_dict=class_parameters_dict,
        iterations=meta_parameters["num_iterations_total"],
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
