import json
import os
from typing import Optional

CELL_CLASS = "VegCell"
DEFAULT_BATCH_PARAMETERS_PATH = os.getenv(
    "DEFAULT_BATCH_PARAMETERS_PATH", "vegetation/config/batch_parameters.json"
)
DEFAULT_ATTRIBUTE_ENCODINGS_PATH = os.getenv(
    "DEFAULT_ATTRIBUTE_ENCODINGS_PATH", "vegetation/config/attribute_encodings.json"
)
DEFAULT_AOI_BOUNDS_PATH = os.getenv(
    "DEFAULT_AOI_BOUNDS_PATH", "vegetation/config/aoi_bounds.json"
)


def convert_user_input(value: any, user_input: str) -> any:
    """Convert user input to match the type of the original value."""
    if not user_input.strip():
        return value

    original_type = type(value)
    try:
        if isinstance(value, list):
            # Strip brackets and split on commas
            cleaned_input = user_input.strip("[]() ").split(",")
            # Convert each element to match type of first element in original list
            if value:
                return [
                    convert_user_input(value[0], item.strip()) for item in cleaned_input
                ]
            return [
                item.strip() for item in cleaned_input
            ]  # If empty list, return strings

        if isinstance(value, bool):
            return user_input.lower() in ("true", "t", "yes", "y", "1")
        elif isinstance(value, int):
            return int(user_input)
        elif isinstance(value, float):
            return float(user_input)
        else:
            return user_input
    except ValueError:
        print(f"Invalid input. Expected type {original_type.__name__}")
        return value


def get_interactive_params(
    batch_parameters_path: Optional[str] = DEFAULT_BATCH_PARAMETERS_PATH,
    attribute_encodings_path: Optional[str] = DEFAULT_ATTRIBUTE_ENCODINGS_PATH,
    aoi_bounds_path: Optional[str] = DEFAULT_AOI_BOUNDS_PATH,
) -> dict:
    # Load configs first
    batch_parameters = json.load(open(batch_parameters_path, "r"))
    simulation_parameters = None
    overwrite = False

    # Let user select simulation or enter new name
    print("\nAvailable simulations (or enter new name):")
    for idx, sim in enumerate(batch_parameters.keys()):
        if sim != "__interactive_default":
            print(f"{idx}: {sim}")

    while True:
        selection = input("\nSelect simulation number or enter new name: ")
        try:
            # Try numeric selection first (0-indexed)
            sim_idx = int(selection) - 1
            simulation_name = list(
                k for k in batch_parameters.keys() if k != "__interactive_default"
            )[sim_idx]
            print("Selected:", simulation_name)

            parameters_dict = construct_model_run_parameters_from_file(
                simulation_name=simulation_name,
                batch_parameters_path=batch_parameters_path,
                attribute_encodings_path=attribute_encodings_path,
                aoi_bounds_path=aoi_bounds_path,
            )

            print(f"Running simulation {simulation_name} with batch parameters:")
            for key, value in parameters_dict["model_run_parameters"].items():
                print(f"{key}: {value}")

            return parameters_dict

        except ValueError:
            # If not numeric, treat as new simulation name
            simulation_name = selection
            if "__interactive_default" not in batch_parameters:
                print("Error: __interactive_default template not found in parameters")
                exit(1)
            simulation_parameters = batch_parameters["__interactive_default"].copy()
            break
        except IndexError:
            print("Invalid selection. Try again.")

    output_path = (
        os.getenv("MESA_RESULTS_DIR", "/local_dev_data/mesa_results/")
        + f"{simulation_name}.csv"
    )
    if os.path.exists(output_path):
        print(f"Output path {output_path} exists.")
        overwrite = input("Overwrite? [y/n]: ")
        if overwrite.lower() != "y":
            print("Exiting.")
            exit()
        else:
            overwrite = True

    if not simulation_parameters:
        simulation_parameters = batch_parameters[simulation_name]
    meta_parameters = simulation_parameters["meta_parameters"]
    model_run_parameters = simulation_parameters["model_run_params"]

    # Interactive selection of cell attributes to save
    cell_attributes_to_save = []
    if attribute_encodings_path:
        attribute_encodings = json.load(open(attribute_encodings_path, "r"))
        veg_cell_attrs = attribute_encodings[CELL_CLASS]

        print("\nSelect cell attributes to save (y/n for each):")
        for attr, details in veg_cell_attrs.items():
            desc = details.get("description", "No description available")
            save_attr = input(f"{attr} ({desc}) [y/n]: ").lower()
            if save_attr == "y":
                cell_attributes_to_save.append(attr)

        if cell_attributes_to_save == []:
            print("Warning: No attributes selected to save")
            cell_attributes_to_save = None

    # Interactive override of meta parameters
    print("\nMeta parameters (press Enter to keep default):")
    for key, value in meta_parameters.items():
        user_input = input(f"{key} [{value}]: ")
        if user_input.strip():
            meta_parameters[key] = convert_user_input(value, user_input)

    # Interactive override of model parameters
    print("\nModel parameters (press Enter to keep default):")
    for key, value in model_run_parameters.items():
        user_input = input(f"{key} [{value}]: ")
        if user_input.strip():
            model_run_parameters[key] = convert_user_input(value, user_input)

    # Handle bounds
    aoi_bounds = None
    if aoi_bounds_path:
        aoi_bounds_options = json.load(open(aoi_bounds_path, "r"))
        print("\nAvailable bounds:")
        for idx, (key, bounds) in enumerate(aoi_bounds_options.items()):
            print(f"{idx}: {key} {bounds}")
        while True:
            try:
                bounds_idx = int(input("\nSelect bounds number: "))
                aoi_bounds = list(aoi_bounds_options.values())[bounds_idx]
                break
            except (ValueError, IndexError):
                print("Invalid selection. Try again.")

    # Handle attribute encodings
    attribute_encodings = None
    if attribute_encodings_path:
        attribute_encodings = json.load(open(attribute_encodings_path, "r"))
        attribute_encodings = attribute_encodings[CELL_CLASS]

    model_run_parameters["simulation_name"] = simulation_name

    parameters_dict = {
        "meta_parameters": meta_parameters,
        "model_run_parameters": model_run_parameters,
        "attribute_encodings": attribute_encodings,
        "aoi_bounds": aoi_bounds,
        "cell_attributes_to_save": cell_attributes_to_save,
        "overwrite": overwrite,
    }

    return parameters_dict


# TODO: Implement early stopping when all the JOTR die off
# Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/18

# TODO: Figure out how model_params is passed to mesa
# Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/38
# This is causing issues regarding how many sims are actually run


def construct_model_run_parameters_from_file(
    simulation_name: str,
    batch_parameters_path: str,
    attribute_encodings_path: Optional[str],
    aoi_bounds_path: Optional[str],
):
    # Read in the configs
    batch_parameters = json.load(open(batch_parameters_path, "r"))
    simulation_parameters = batch_parameters[simulation_name]
    # Get meta parameters for this batch run (things not relevant to specific model runs)
    meta_parameters = simulation_parameters["meta_parameters"]

    # Get the model parameters for this particular simulation
    model_run_parameters = simulation_parameters["model_run_params"]

    # Get the cell-level attributes to save to zarr
    cell_attributes_to_save = simulation_parameters["cell_attributes_to_save"]

    # Replace the string key for bounds with the actual bounds, if provided
    if aoi_bounds_path is not None:
        aoi_bounds_options = json.load(open(aoi_bounds_path, "r"))
        aoi_bounds_key = simulation_parameters["bounds_key"]
        aoi_bounds = aoi_bounds_options[aoi_bounds_key]
        del simulation_parameters["bounds_key"]

    assert len(aoi_bounds) == 4
    assert all([isinstance(x, float) for x in aoi_bounds])

    # Include the attribute encodings, for zarr to save within metadata, if provided
    if attribute_encodings_path is not None:
        attribute_encodings = json.load(open(attribute_encodings_path, "r"))
        attribute_encodings = attribute_encodings[CELL_CLASS]

        # TODO: This might be worth enforcing for all simulations
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/39
        #  (either provided at runtime or in  the config file, but since
        # the attrs are within the agent class, it seems like it in config)
        if cell_attributes_to_save is not None:
            assert all(
                [attr in attribute_encodings.keys() for attr in cell_attributes_to_save]
            )

    model_run_parameters["simulation_name"] = simulation_name

    return {
        "meta_parameters": meta_parameters,
        "model_run_parameters": model_run_parameters,
        "attribute_encodings": attribute_encodings,
        "aoi_bounds": aoi_bounds,
        "cell_attributes_to_save": cell_attributes_to_save,
    }
