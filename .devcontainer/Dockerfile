# First, grab a Unix image with pixi installed
FROM ghcr.io/prefix-dev/pixi:0.18.0

# Copy over install scripts - this is a good way to keep the Dockerfile clean and readable
COPY .devcontainer/scripts .devcontainer/scripts

# Install git, ssh
RUN .devcontainer/scripts/install_git_and_ssh.sh

# Copy over pixi toml and pyproject.toml
COPY pixi.toml pixi.toml
COPY pixi.lock pixi.lock

# TODO: Pixi is invalidating docker cache here for some reason - it would be better 
# to do a multi-stage build and only copy over the source code at the end
# See https://github.com/pavelzw/pixi-docker-example/blob/main/3-multi-stage/Dockerfile

# Install pixi dependencies
RUN pixi install

# Now, copy python source code into the image - by doing this last, we can avoid re-installing ALL dependencies if just the source code changes
COPY vegetation vegetation

# Finally, keep the container running so that we can attach to it
CMD tail -f /dev/null