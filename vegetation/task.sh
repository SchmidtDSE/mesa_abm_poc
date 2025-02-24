#/bin/bash

# Install the pixi environment
pixi install

# Start the Pixi shell
eval "$(pixi shell-hook)"

# Create temp directory if it doesn't exist
mkdir -p /tmp

# Modify JSON template with env var (INITIAL_AGENTS_KEY)
jq --arg key "$INITIAL_AGENTS_KEY" '.k8s_run.initial_agents_key = $key' \
vegetation/config/batch_parameters.json > /tmp/modified_params.json

# Run the simulation, using the modified batch json
python -m vegetation.batch.run \
--batch_parameters_json /tmp/modified_params.json \
--simulation_name k8s_run \
--zarr_store_type directory \
--overwrite