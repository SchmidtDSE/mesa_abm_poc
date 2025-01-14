import os
from pathlib import Path

## GLOBALS - these should not change between runtime environment
DEM_STAC_PATH = "https://planetarycomputer.microsoft.com/api/stac/v1/"

## LOCALS - to be used with a .env file, but some defaults are provided, since
## the devcontainer should make this standard. The one environment outside of the
## devcontainer is the github actions runner, so we provide this to override the defaults.
PACKAGE_PATH = Path(__file__).resolve().parent.parent
SAVE_LOCAL_STAC_CACHE = os.getenv("SAVE_LOCAL_STAC_CACHE", True)
INITIAL_AGENTS_PATH = f"{PACKAGE_PATH}/data/initial_agents.json"
DEM_STAC_PATH = "https://planetarycomputer.microsoft.com/api/stac/v1/"
LOCAL_STAC_CACHE_FSTRING = (
    f"{PACKAGE_PATH}/.local_dev_data/{{band_name}}_{{bounds_md5}}.tif"
)
