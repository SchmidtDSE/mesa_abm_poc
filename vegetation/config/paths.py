import os

## GLOBALS - these should not change between runtime environment
DEM_STAC_PATH = "https://planetarycomputer.microsoft.com/api/stac/v1/"

## LOCALS - to be used with a .env file, but some defaults are provided, since
## the devcontainer should make this standard. The one environment outside of the
## devcontainer is the github actions runner, so we provide this to override the defaults.
INITIAL_AGENTS_PATH = os.getenv(
    "INITIAL_AGENTS_PATH",
    "/workspaces/mesa_abm_poc/vegetation/data/initial_agents.json",
)
LOCAL_STAC_CACHE_FSTRING = os.getenv(
    "LOCAL_STAC_CACHE_FSTRING",
    "/workspaces/mesa_abm_poc/.local_dev_data/{band_name}_{bounds_md5}.tif",
)
SAVE_LOCAL_STAC_CACHE = os.getenv("SAVE_LOCAL_STAC_CACHE", True)
