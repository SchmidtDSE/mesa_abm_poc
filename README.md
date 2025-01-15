## Dev setup

### Using devcontainer

If going the dev container route, you will need the following:

- Docker (cli, but optionally the desktop app)
- VSCode, and the `Dev Containers` extension
- `ssh` installed on the host machine, to access git from within
- A folder `local_dev_data` needs to be created in your home directory
- a `.env` file in the `.devcontainer` folder, in the following format:

```
DEM_STAC_PATH = "https://planetarycomputer.microsoft.com/api/stac/v1/"
INITIAL_AGENTS_PATH = "/workspaces/mesa_abm_poc/vegetation/data/initial_agents.json"
LOCAL_STAC_CACHE_FSTRING = "/workspaces/mesa_abm_poc/vegetation/.local_dev_data/{band_name}_{bounds_md5}.tif"
SAVE_LOCAL_STAC_CACHE = True
DOCKER_HOST_STAC_CACHE_FSTRING = "/local_dev_data/mesa_exog_cache/{band_name}_{bounds_md5}.tif"
```

After cloning the repo, you will need to open it in VSCode and run the following command:

- `Cmd + Shift + P -> Dev Containers: Reopen in Container`

## Simulations

The demo simulation here is derived from `mesa-geo`'s [Rainfall Model](https://github.com/projectmesa/mesa-examples/tree/main/gis/rainfall).

## Running the Solara server

To run Solara, it's recommended to use the included VSCode launch config (which will be detected automatically by VSCode within the debug panel). Simply fire it up and click the localhost link to use the Solara dashboard.

Alternatively, the simulation can be run the same way (without debugging) via the following command:

```bash
pixi run vegetation
```

## Known Issues

- For some weird reason, after adding interactivity, the solara app only runs after being reloaded after initial build. This can be triggered by saving any file within the repo, and things seem to work fine after that - you can even make source edits and re-run, which is a nice workflow. Weird!

- Sliders don't seem to change model inits whatsoever - and docs don't show any explicit way to access them, seems to just 'happen' when registering model params?

- Occasionally Solara appears to never render (stuck on "Loading App"). Simply rebuilding (not from cache) seems to fix it, and it seems to happen after changes are made to the `SolaraViz` class from mesa-geo - could have something to do with autoreload, but not sure. 