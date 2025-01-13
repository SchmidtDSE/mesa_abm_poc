from pathlib import Path


PACKAGE_PATH = Path(__file__).resolve().parent.parent
INITIAL_AGENTS_PATH = f"{PACKAGE_PATH}/data/initial_agents.json"

DEM_STAC_PATH = "https://planetarycomputer.microsoft.com/api/stac/v1/"
LOCAL_STAC_CACHE_FSTRING = (
    f"{PACKAGE_PATH}/.local_dev_data/{{band_name}}_{{bounds_md5}}.tif"
)
