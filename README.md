# mediatools
This repo houses the `Dockerfile` to create a Docker container for Jackett with Transmission and SickChill.
This `Dockerfile` should work on either `x86_64` or `arm64` processor architectures. It has been tested on `x86_64`.

This is based on the `sickcont` container created by the Sergong. The git repo is [here](https://github.com/Sergong/sickcont).
The Jackett install in the `Dockerfile` was taken from the folks at linuxserver. Their git repo is [here](https://github.com/linuxserver/docker-jackett).

It also contains a compose.yaml file to start the container with docker, tested on Docker on linux.

It is assumed that you know how to build docker containers from a Dockerfile.

## Directory Structure

Ensure that the directory structure referenced by the volume mounts in the compose.yaml file are  present on your system.

So for the docker compose example here `compose.yaml`, you'd need to create the following directories under the config directory in this repo:
- `mkdir config/{downloads,tv}`

