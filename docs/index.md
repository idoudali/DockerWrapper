# `docker_wrapper` User Guide

- [`docker_wrapper` User Guide](#docker_wrapper-user-guide)
  - [Installation](#installation)
  - [Overview](#overview)
  - [Code Organization](#code-organization)
  - [Usage Mode](#usage-mode)
    - [Docker-Image Folder Layout](#docker-image-folder-layout)
    - [Image registration](#image-registration)

## Installation

Install [uv](https://docs.astral.sh/uv/), then sync the project environment
(runtime, development, and docs groups):

```bash
uv sync --all-groups
```

The same step is available as `make install`. To interact with the CLI:

```bash
uv run docker_wrapper --help
```

Consumer repositories should add this package with `uv add docker-wrapper`
(or a path/git dependency) rather than a `requirements.txt` pin.

## Overview

The goal of this library is to provide a convenient wrapper around Docker to allow
us to perform common development and CI tasks. The intent is to have a number
development Docker images that can enable us to have reproducible builds.

The type of tasks we want to be able to automate are:

- Build the docker images, and enable introducing a "hierarchy" of images
where common dependencies are factored out.
- Pull / push docker images to the docker registries, which could be multiple
based on our CI needs.
- Create development container that the user can work side
- Allow to run commands inside temporary containers that could be used in our CI.

## Code Organization

We are providing a common Docker library called [docker_wrapper](/src/docker_wrapper/docker_helpers.py)
where we have a base class `DockerImage` that implements the basic wrapper logic.

A CLI interface is implemented under [cli.py](/src/docker_wrapper/cli.py) the user can call function
`create_cli` to register a CLI in the target's repos entrypoint helper script.

## Usage Mode

The intent is for this library to be a uv dependency of each repo and be consumed
by the `repo-cli.py` script ( or any other entrypoint script ) of the repo. Then in each repo
we are doing to define a `docker-images` folder, similar to [sample-images](/sample-images) folder of
this folder.

### Docker-Image Folder Layout

The expectation is that the `docker-images` folder contains a single-level hierarchy of folder, where
each folder has the following layout:

```
ubuntu_base/
├── Docker
│   ├── Dockerfile
│   └── entrypoint.sh
├── docker_wrapper_extensions.py
├── __init__.py
```

Each docker image has a script called `docker_wrapper_extensions.py` where we implement "logic" specific
to that docker image. Inside that file we are defining a `DockerImage` class as follows:

```python
import os

import docker_wrapper


class DockerImage(docker_wrapper.DockerImage):
    """ubuntu_base docker image."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "ubuntu_base"
        self.docker_folder = os.path.realpath(
            os.path.join(os.path.realpath(__file__), "../Docker")
        )
        print(self.docker_folder)
```

We also expect that there is a `Docker` folder where we have the `Dockerfile` and anyother script (e.g. entrypoint.sh)
that we want to be added to the Docker image.


### Image registration

In [cli.py](/src/docker_wrapper/cli.py) we provide function `create_cli` to "register" any images that we have available.
The `create_cli` takes as an argument the path of the top-level folder where all images are located. It expects that
it would find per image a file layout similar to the one described above. `create_cli` checks that there is a `Docker` subfolder
per image and import the `docker_wrapper_extensions.py` file of each image, find the `DockerImage` class and "register" it with
the rest of the CLI commands.
