from vegetation.batch import TST_JOTR_BOUNDS, batch_run
from patch.model import Vegetation
from numpy import arange
import pandas as pd
import pytest


def test_batch_run_basic():
    # Set up minimal test parameters
    test_params = {
        "num_steps": [3],  # Reduced from 100 to 3 steps
        "management_planting_density": [0.0, 0.5],  # Just test two values
        "export_data": [False],
        "bounds": [TST_JOTR_BOUNDS],
    }

    # Run simulation with minimal parameters
    results = batch_run(
        Vegetation,
        parameters=test_params,
        iterations=1,
        max_steps=3,
        number_processes=1,
        data_collection_period=1,
        display_progress=False,
    )

    # Basic validation
    assert isinstance(results, pd.DataFrame)
    assert len(results) > 0

    # Check expected columns exist
    expected_columns = {
        "Run",
        "iteration",
        "Step",
        "management_planting_density",
        "num_steps",
        "export_data",
    }
    assert all(col in results.columns for col in expected_columns)

    # Verify we got correct number of steps
    assert results["Step"].max() == 3

    # Verify we got results for both density values
    assert len(results["management_planting_density"].unique()) == 2
