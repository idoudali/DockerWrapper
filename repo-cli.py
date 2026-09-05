#!/usr/bin/env python
"""Example repository CLI that registers sample Docker images."""

from pathlib import Path
import socket

import typer
import yaml

import docker_wrapper

REPO_DIR = Path(__file__).parent.absolute()
CONFIG_FILE_PATH = REPO_DIR / "example-environment-cfg.yml"
ENV_CONFIG = {}


def get_domain() -> str:
    """Return the fully qualified domain name of this host."""
    return socket.getfqdn()


def read_config_file(file_path: Path) -> dict[str, object]:
    """Load environment configuration from a YAML file.

    Args:
        file_path: Path to the YAML configuration file.

    Returns:
        Parsed configuration mapping.
    """
    with open(file_path) as file:
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
    ) -> None:
        """Configure the CLI for the selected environment.

        Args:
            env_name: Environment name from the YAML config. The sample
                entrypoint always uses the ``local`` environment.
        """
        global ENV_CONFIG
        # For the purpose of this example, we will use the local environment only
        ENV_CONFIG = all_config_data["local"]
        docker_wrapper.set_env_config(ENV_CONFIG)

    app.add_typer(
        docker_wrapper.create_cli(image_dir="sample-images", env_config_arg=ENV_CONFIG),
        name="docker",
    )

    app()
