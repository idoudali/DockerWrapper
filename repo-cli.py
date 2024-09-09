#!/usr/bin/env python

from pathlib import Path
import socket

import typer
import yaml

import docker_wrapper

REPO_DIR = Path(__file__).parent.absolute()
CONFIG_FILE_PATH = REPO_DIR / "example-environment-cfg.yml"
ENV_CONFIG = {}


def get_domain():
    return socket.getfqdn()


def read_config_file(file_path):
    with open(file_path, "r") as file:
        config_data = yaml.safe_load(file)
    return config_data


if __name__ == "__main__":

    all_config_data = read_config_file(CONFIG_FILE_PATH)

    app = typer.Typer()

    # Create a top level command for the repo CLI
    #
    @app.callback()
    def main(
        env_name: str = typer.Option("local", help="Environment name"),
    ):
        global ENV_CONFIG
        # For the purpose of this example, we will use the local environment only
        ENV_CONFIG = all_config_data["local"]
        docker_wrapper.set_env_config(ENV_CONFIG)

    app.add_typer(
        docker_wrapper.create_cli(image_dir="sample-images", env_config_arg=ENV_CONFIG),
        name="docker",
    )

    app()
