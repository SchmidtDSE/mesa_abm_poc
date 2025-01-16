#/bin/bash

apt-get update && apt-get install -y git openssh-client curl bash-completion

# Get installed git version and remove 'git version ' prefix
GIT_VERSION=$(git --version | cut -d' ' -f3)

# Configure git autocompletion for branches using detected version
curl "https://raw.githubusercontent.com/git/git/v${GIT_VERSION}/contrib/completion/git-completion.bash" -o /tmp/.git-completion.bash
source /tmp/.git-completion.bash