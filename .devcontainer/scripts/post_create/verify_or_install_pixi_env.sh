#!/bin/bash

# if /workspaces/mesa_abm_poc/.pixi exists, delete its contents
# this should not be triggered unless we rebuild the container 
# without cache
if [ -d "/workspaces/mesa_abm_poc/.pixi" ]; then
  rm -rf /workspaces/mesa_abm_poc/.pixi/*
fi

# Ensure that the jovyan user owns the .pixi directory
sudo chown -R jovyan:root .pixi

# Install pixi dependencies according to pixi.toml and pixi.lock
pixi install