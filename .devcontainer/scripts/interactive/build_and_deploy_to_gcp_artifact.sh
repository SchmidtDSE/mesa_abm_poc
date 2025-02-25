#/bin/bash

# Note: this script will NOT run in the dev container since docker is not installed in the dev container!
# It is included here for reference - this will need to be run on your local machine. As such, it is not executable.

# Build and tag the image
docker build   -t us-west1-docker.pkg.dev/dse-nps/mesa-abm-poc/mesa-abm-poc:latest \
  -f .devcontainer/Dockerfile \
  --build-arg IS_DEVCONTAINER=False \
  .

# Push the image to GCP Artifact Registry
docker push us-west1-docker.pkg.dev/dse-nps/mesa-abm-poc/mesa-abm-poc:latest