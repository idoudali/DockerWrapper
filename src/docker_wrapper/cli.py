#!/usr/bin/env python3

from enum import Enum
import importlib
import importlib.util
import logging
import os
from pathlib import Path
from typing import Callable, Dict, List, NewType, Optional, Union

import typer

from . import docker_helpers

_LOG_LEVEL_STRINGS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]


class LoggingLevel(str, Enum):
    """Enum holding the different logging argument values."""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


"""Dictionary of all docker images specified by the CLI"""
DockerImages = {}

WRAPPER_EXTENSIONS: Dict[str, Callable[[], docker_helpers.DockerImage]] = {}

EnumClassType = NewType("EnumClassType", Enum)


class TEST:
    def __init__(self, month: str):  # Several values per member are possible.
        self.month = month


def create_image(image_name: str) -> docker_helpers.DockerImage:
    if image_name not in WRAPPER_EXTENSIONS:
        typer.echo(f"Unknown Image {image_name}")
        raise typer.Exit(1)
    image = WRAPPER_EXTENSIONS[image_name]()
    return image


def create_cli(image_names: Union[str, EnumClassType]) -> typer.Typer:
    app = typer.Typer()

    @app.callback()
    def main(
        image_dir: Path,
        log_level: LoggingLevel = typer.Option(LoggingLevel.INFO, help="Set logging level"),
        show_choices: bool = True,
    ) -> None:
        """
        Provide the docker wrapper CLI
        """
        # Configure the logging level of the run
        if log_level not in _LOG_LEVEL_STRINGS:
            message = "invalid choice: {0} (choose from {1})".format(log_level, _LOG_LEVEL_STRINGS)
            typer.echo(message)
            typer.Exit(code=1)
        log_level_int = getattr(logging, log_level, logging.INFO)
        # check the logging log_level_choices have not changed from our expected values
        assert isinstance(log_level_int, int)
        logging.basicConfig(level=log_level_int)
        # Find all available docker images under the image_dir folder
        # Assume that each folder is a separate docker image and there is no nestting
        # Expected that each folder should have a docker_wrapper_extensions.py Python script
        # and a Docker folder with ant necessary files
        for root, dirs, _ in os.walk(os.path.realpath(image_dir), topdown=True):
            for dir in dirs:
                if "Docker" == dir:
                    image_name = os.path.basename(root)
                    DockerImages[image_name] = os.path.realpath(root)
        logging.debug(f"Found docker images: {DockerImages}")
        # Load the docker_wrapper_extensions.py, import it as a module and get a callable
        # object for the DockerImage class object that each file contains
        for iname, ipath in DockerImages.items():
            spec = importlib.util.spec_from_file_location(
                "docker_wrapper_extensions", os.path.join(ipath, "docker_wrapper_extensions.py")
            )
            mod = importlib.util.module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(mod)  # type: ignore
            image_constructor = mod.DockerImage
            WRAPPER_EXTENSIONS[iname] = image_constructor

    @app.command()
    def prompt(
        image_name: image_names,  # type: ignore
        project_dir: Path = typer.Option(".", help="Path of the repo top-level"),
        nvidia_docker: bool = typer.Option(False, help="Use NVidia-docker"),
        privileged: bool = typer.Option(False, help="Enable Docker privileged mode"),
        port: Optional[List[str]] = typer.Option(None, help="Port to forward from Docker"),
    ) -> None:
        image = create_image(image_name)
        image.run(
            prompt=True,
            project_dir=project_dir,
        )

    @app.command()
    def build(
        image_name: image_names,  # type: ignore
    ) -> None:
        image = create_image(image_name)
        image.build_image()

    @app.command()
    def push(
        image_name: image_names,  # type: ignore
    ) -> None:
        image = create_image(image_name)
        image.push()

    @app.command()
    def pull(
        image_name: image_names,  # type: ignore
    ) -> None:
        image = create_image(image_name)
        image.pull()

    return app


def main() -> None:
    image_names = str

    app = create_cli(image_names)  # type: ignore
    app()


# Allow the script to be run standalone (useful during development).
if __name__ == "__main__":
    main()
