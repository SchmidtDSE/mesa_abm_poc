# Use a jupyter base image for cirrus
FROM quay.io/jupyter/minimal-notebook:latest

# Create a user-writable space outside $HOME for apps to live.
ENV XDG_DATA_HOME=/opt/share
ENV PIXI_HOME $XDG_DATA_HOME/pixi
ENV PATH $PIXI_HOME/bin:$PATH
ENV GRANT_SUDO=yes

USER root
RUN mkdir /opt/share && chown -R $NB_USER:users /opt/share

# Install code server
RUN curl -fsSL https://code-server.dev/install.sh | sh && rm -rf .cache 

# Change from root to $NB_USER
USER $NB_USER

# codeserver extensions
RUN echo "ms-python.python ms-toolsai.jupyter continue.continue" | xargs -n 1 code-server --install-extension
RUN mamba install jupyter-vscode-proxy

# Install pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash

# Copy over install scripts - this is a good way to keep the Dockerfile clean and readable
COPY .devcontainer/scripts .devcontainer/scripts

# Install git, ssh and other tools contained in `scripts/run_on_build.sh`
RUN .devcontainer/scripts/run_on_build.sh

# Copy over pixi toml and pyproject.toml
COPY pixi.toml pixi.toml
COPY pixi.lock pixi.lock

# Now, copy python source code into the image - by doing this last, we can avoid re-installing ALL dependencies if just the source code changes
COPY vegetation vegetation

# Finally, keep the container running so that we can attach to it
CMD tail -f /dev/null