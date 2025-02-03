#/bin/bash

apt-get update && apt-get install -y git openssh-client curl bash-completion

# To enable bash completion for git
echo "source /usr/share/bash-completion/completions/git" >> ~/.bashrc