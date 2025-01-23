#!/bin/bash

# if /workspaces/mesa_abm_poc/.pixi exists, delete its contents
# this should not be triggered unless we rebuild the container 
# without cache
if [ -d "/workspaces/mesa_abm_poc/.pixi" ]; then
  rm -rf /workspaces/mesa_abm_poc/.pixi/*
fi

pixi install