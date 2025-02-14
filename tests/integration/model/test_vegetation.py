import pytest
import numpy as np
from vegetation.model.vegetation import Vegetation


class TestVegetationInit:
    def test_basic_initialization(self, base_model):
        assert base_model.num_steps == 10
        assert base_model.management_planting_density == 0.01
        assert not base_model._on_start_executed
        assert base_model.replicate_idx is None

    def test_verify_class_attributes_fails_without_aoi_bounds(self):
        with pytest.raises(ValueError):
            Vegetation()


class TestVegetationClassMethods:
    def test_set_attribute_encodings(self, test_parameters_dict):
        test_attribute_encodings = test_parameters_dict["attribute_encodings"]
        Vegetation.set_attribute_encodings(test_attribute_encodings)
        assert Vegetation._attribute_encodings == test_attribute_encodings

    def test_set_aoi_bounds(self, test_parameters_dict):
        test_aoi_bounds = test_parameters_dict["aoi_bounds"]
        Vegetation.set_aoi_bounds(test_aoi_bounds)
        assert Vegetation._aoi_bounds == test_aoi_bounds


class TestVegetationMetrics:
    def test_update_metrics(self, base_model_with_on_start_executed):
        base_model_with_on_start_executed.update_metrics()

        assert np.isclose(base_model_with_on_start_executed.mean_age, 80 / 6)
        assert base_model_with_on_start_executed.n_seeds == 1
        assert base_model_with_on_start_executed.n_seedlings == 0
        assert base_model_with_on_start_executed.n_juveniles == 5
        assert base_model_with_on_start_executed.n_adults == 0
        assert base_model_with_on_start_executed.n_breeding == 0
        assert base_model_with_on_start_executed.n_dead == 0
