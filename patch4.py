import os

with open(".github/workflows/build.yml", 'r') as f:
    content = f.read()

# We need to distinguish between ubuntu-latest without container (which needs sudo)
# and ubuntu-latest with container (which doesn't have sudo and runs as root).
# The build job runs on ubuntu-latest, no container. It needs `sudo apt-get` and `sudo chown` and `sudo sed`.
# The build-linux-buildbot job in tools.yml and build.yml runs with `container: registry.gitlab.com/openwrt/buildbot/buildworker-3.4.1`
