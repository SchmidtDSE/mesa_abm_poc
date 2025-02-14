import pytest
from unittest.mock import Mock
from vegetation.model.vegetation import Vegetation
from vegetation.batch.routes import (
    construct_model_run_parameters_from_file,
)
from pathlib import Path
import os
import shutil


@pytest.fixture(autouse=True)
def clean_test_environment():
    mesa_csv_dir = os.getenv("MESA_RESULTS_DIR")
    mesa_csv_dir_pytest = Path(mesa_csv_dir) / "pytest.csv"
    if mesa_csv_dir_pytest.exists():
        mesa_csv_dir_pytest.unlink()

    mesa_zarr_dir = "vegetation.zarr/pytest"
    mesa_zarr_dir_pytest = Path(mesa_zarr_dir)
    if mesa_zarr_dir_pytest.exists():
        shutil.rmtree(mesa_zarr_dir_pytest)

    # Run the test
    yield

    # Clean up after the test
    pass


@pytest.fixture
def mock_study_area():
    mock = Mock()
    mock.raster_layer.width = 100
    mock.raster_layer.height = 100
    mock.crs.to_string.return_value = "EPSG:4326"
    return mock


@pytest.fixture
def base_model(test_parameters_dict):
    # Set required class attributes

    test_aoi_bounds = test_parameters_dict["aoi_bounds"]
    test_attribute_encodings = test_parameters_dict["attribute_encodings"]
    test_cell_attributes_to_save = test_parameters_dict["cell_attributes_to_save"]

    Vegetation.set_aoi_bounds(test_aoi_bounds)
    Vegetation.set_attribute_encodings(test_attribute_encodings)
    Vegetation.set_cell_attributes_to_save(test_cell_attributes_to_save)

    return Vegetation(simulation_name="pytest", num_steps=10, ignore_zarr_warning=True)


@pytest.fixture
def base_model_with_on_start_executed(base_model):
    base_model._on_start()
    return base_model


@pytest.fixture
def test_parameters_dict():
    test_assets_dir = os.getenv(
        "TEST_ASSETS_DIR", "/workspaces/mesa_abm_poc/tests/assets"
    )
    test_aoi_bounds_path = Path(test_assets_dir) / "configs" / "test_aoi_bounds.json"
    test_batch_parameters_path = (
        Path(test_assets_dir) / "configs" / "test_batch_parameters.json"
    )
    test_attribute_encodings_path = (
        Path(test_assets_dir) / "configs" / "test_attribute_encodings.json"
    )

    parameters_dict = construct_model_run_parameters_from_file(
        simulation_name="pytest",
        batch_parameters_path=test_batch_parameters_path,
        aoi_bounds_path=test_aoi_bounds_path,
        attribute_encodings_path=test_attribute_encodings_path,
    )

    return parameters_dict
