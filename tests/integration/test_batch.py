from vegetation.batch import TST_JOTR_BOUNDS, batch_run
from vegetation.model.vegetation import Vegetation
import pandas as pd


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

    results_pd = pd.DataFrame(results)

    # Basic validation
    assert isinstance(results_pd, pd.DataFrame)
    assert len(results) > 0

    # Check expected columns exist
    expected_columns = {"RunId", "iteration", "Step"}
    assert all(col in results_pd.columns for col in expected_columns)
