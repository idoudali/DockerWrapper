#!/usr/bin/env python3

"""Command line interface of the Docker Wrapper module
"""

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
    """Enum holding the different logging argument values.

    Args:
        str (_type_): String Enumeration
        Enum (_type_): Enum
    """

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


WRAPPER_EXTENSIONS: Dict[str, Callable[[], docker_helpers.DockerImage]] = {}

EnumClassType = NewType("EnumClassType", Enum)


class TEST:
    def __init__(self, month: str):  # Several values per member are possible.
        self.month = month


def find_extensions(image_dir: Path) -> Dict[str, Callable[[], docker_helpers.DockerImage]]:
    """Find all available Docker images and extension modules that enable working with them

    Args:
        image_dir (Path): Path containing the docker images.

    Returns:
        Dict[str, Callable[[], docker_helpers.DockerImage]]: Dictionary of docker image names and
        object constructors we can call.
    """
    # Find all available docker images under the image_dir folder
    # Assume that each folder is a separate docker image and there is no nestting
    # Expected that each folder should have a docker_wrapper_extensions.py Python script
    # and a Docker folder with ant necessary files
    docker_images = {}
    for root, dirs, _ in os.walk(os.path.realpath(image_dir), topdown=True):
        for dir in dirs:
            if "Docker" == dir:
                image_name = os.path.basename(root)
                docker_images[image_name] = os.path.realpath(root)
    logging.debug(f"Found docker images: {docker_images}")
    # Load the docker_wrapper_extensions.py, import it as a module and get a callable
    # object for the DockerImage class object that each file contains
    extensions = {}
    for iname, ipath in docker_images.items():
        spec = importlib.util.spec_from_file_location(
            "docker_wrapper_extensions", os.path.join(ipath, "docker_wrapper_extensions.py")
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        spec.loader.exec_module(mod)  # type: ignore
        image_constructor = mod.DockerImage
        extensions[iname] = image_constructor
    return extensions


def create_image(image_name: str) -> docker_helpers.DockerImage:
    """Instantiate an DockerImage object (or its subclass) for the specified
    Image

    Args:
        image_name (str): Name of the image to create an image for.

    Raises:
        typer.Exit: Failure if the image is not found

    Returns:
        docker_helpers.DockerImage: Docker image object to be used to interact with it.
    """
    if image_name not in WRAPPER_EXTENSIONS:
        typer.echo(f"Unknown Image {image_name}")
        raise typer.Exit(1)
    image = WRAPPER_EXTENSIONS[image_name]()
    return image


def create_cli(
    image_names: Union[str, EnumClassType], image_dir: Optional[str] = None
) -> typer.Typer:
    """Create the command line interface of the Docker Wrapper

    Args:
        image_names (Union[str, EnumClassType]): Union. pass a string if we do not
            know the list of functions ahead of time, or an Enum with the allowed list
            of images to use.
        image_dir (Optional[str], optional): Direcotry where the Docker image Dockerfiles and
            related code are located. Defaults to None.

    Returns:
        typer.Typer: Typer class wit the registered command line arguments. See the main()
        function how an object can be instantiated.
    """
    app = typer.Typer()

    @app.callback()
    def main(
        image_dir: Path = typer.Argument(image_dir),
        log_level: LoggingLevel = typer.Option(LoggingLevel.INFO, help="Set logging level"),
    ) -> None:
        """Main command arguments

        Args:
            image_dir (Path, optional): Path where images are stored.
                Defaults to typer.Argument(image_dir).
            log_level (LoggingLevel, optional): Executing logging level. Defaults to
                typer.Option(LoggingLevel.INFO, help="Set logging level").
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
        global WRAPPER_EXTENSIONS
        WRAPPER_EXTENSIONS = find_extensions(image_dir)

    @app.command()
    def prompt(
        image_name: image_names,  # type: ignore
        project_dir: Path = typer.Option(".", help="Path of the repo top-level"),
        nvidia_docker: bool = typer.Option(False, help="Use NVidia-docker"),
        privileged: bool = typer.Option(False, help="Enable Docker privileged mode"),
        port: Optional[List[str]] = typer.Option(None, help="Port to forward from Docker"),
    ) -> None:
        """Prompt subcommand, start a docker container and drop the user inside a prompt

        Args:
            image_name (image_names): Name of the image to use
            nvidia_docker (bool, optional): Enable use of nvidia-docker.
                Defaults to typer.Option(False, help="Use NVidia-docker").
            privileged (bool, optional): Enabled docker privileged mode.
                Defaults to typer.Option(False, help="Enable Docker privileged mode").
            port (Optional[List[str]], optional): List of ports to open in the container.
                Defaults to typer.Option(None, help="Port to forward from Docker").
        """
        image = create_image(image_name)
        image.run(
            prompt=True,
            project_dir=project_dir,
        )

    @app.command()
    def build(
        image_name: image_names,  # type: ignore
    ) -> None:
        """Build a docker image

        Args:
            image_name (image_names): Name of the image to build
        """
        image = create_image(image_name)
        image.build_image()

    @app.command()
    def push(
        image_name: image_names,  # type: ignore
    ) -> None:
        """Push a Docker image to a Docker registry

        Args:
            image_name (image_names): Name of the image to push
        """
        image = create_image(image_name)
        image.push()

    @app.command()
    def pull(
        image_name: image_names,  # type: ignore
    ) -> None:
        """Pull a docker image form a Docker registry

        Args:
            image_name (image_names): Name of the image to pull
        """
        image = create_image(image_name)
        image.pull()

    return app


def main() -> None:
    """Helper main function"""
    image_names = str

    app = create_cli(image_names)  # type: ignore
    app()


# Allow the script to be run standalone (useful during development).
if __name__ == "__main__":
    main()
