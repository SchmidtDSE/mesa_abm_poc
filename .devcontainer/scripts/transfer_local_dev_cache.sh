#!/bin/bash

if [ ! -d "/workspaces/mesa_abm_poc/vegetation/.local_dev_data" ]; then
    mkdir /workspaces/mesa_abm_poc/vegetation/.local_dev_data
fi

cp -r /local_dev_data/mesa_exog_cache/* /workspaces/mesa_abm_poc/vegetation/.local_dev_data