#!/bin/bash

if [ ! -d "/workspaces/mesa_abm_poc/.local_dev_data" ]; then
    mkdir /workspaces/mesa_abm_poc/.local_dev_data
fi

cp -r /local_dev_data/* /workspaces/mesa_abm_poc/.local_dev_data