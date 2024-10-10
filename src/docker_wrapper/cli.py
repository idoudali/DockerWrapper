#!/usr/bin/env python3

"""Command line interface of the Docker Wrapper module
"""

from enum import Enum
import importlib
import importlib.util
import inspect
import logging
import os
from pathlib import Path
import subprocess
from typing import Dict, List, NewType, Optional, Type, Union

import typer

from . import docker_helpers

_LOG_LEVEL_STRINGS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
LOCAL_ENV_CONFIG = {}


class LoggingLevel(str, Enum):
    """
    Enum holding the different logging argument values.

    Attributes:
        CRITICAL (str): Represents the 'CRITICAL' logging level.
        ERROR (str): Represents the 'ERROR' logging level.
        WARNING (str): Represents the 'WARNING' logging level.
        INFO (str): Represents the 'INFO' logging level.
        DEBUG (str): Represents the 'DEBUG' logging level.
    """

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


__WRAPPER_EXTENSIONS: Dict[str, Type[docker_helpers.DockerImage]] = {}
__DOCKER_IMAGE_CLASS_NAME = "DockerImages"

EnumClassType = NewType("EnumClassType", Enum)


def set_env_config(config: Dict[str, str]) -> None:
    """Set the configuration of the repository

    Args:
        config (Dict[str, str]): Configuration of the repository
    """
    global LOCAL_ENV_CONFIG
    LOCAL_ENV_CONFIG = config


def get_env_config() -> Dict[str, str]:
    """Get the configuration of the repository

    Returns:
        Dict[str, str]: Configuration of the repository
    """
    return LOCAL_ENV_CONFIG


def find_extensions(image_dir: Path) -> Dict[str, Type[docker_helpers.DockerImage]]:
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
    if not image_dir:
        return {}
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
    for _, ipath in docker_images.items():
        spec = importlib.util.spec_from_file_location(
            "docker_wrapper_extensions", os.path.join(ipath, "docker_wrapper_extensions.py")
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        spec.loader.exec_module(mod)  # type: ignore
        docker_image_classes = []
        for _, obj in inspect.getmembers(mod):
            if inspect.isclass(obj) and issubclass(obj, docker_helpers.DockerImage):
                docker_image_classes.append(obj)
                # docker_image_classes contains the classes that are of type DockerImage
                extensions[obj.NAME] = obj

    return extensions


def __create_image(image_name: str, **kwargs: Dict[str, str]) -> docker_helpers.DockerImage:
    """Instantiate an DockerImage object (or its subclass) for the specified
    Image

    Args:
        image_name (str): Name of the image to create an image for.
        **kwargs (Dict[str, str]): Additional arguments to pass to the DockerImage object.

    Raises:
        typer.Exit: Failure if the image is not found

    Returns:
        docker_helpers.DockerImage: Docker image object to be used to interact with it.
    """
    if image_name not in __WRAPPER_EXTENSIONS:
        typer.echo(f"Unknown Image {image_name}")
        raise typer.Exit(1)
    image = __WRAPPER_EXTENSIONS[image_name](**kwargs)  # type: ignore
    return image


def __get_image_name_value(image_name: Union[str, EnumClassType]) -> str:
    """Get the string value of image_name

    Args:
        image_name (Union[str, EnumClassType]): Value returned by the CLI

    Returns:
        str: Actual value
    """
    if isinstance(image_name, str):
        return image_name
    return str(image_name.value)


def create_cli(
    image_dir: Optional[str] = None, env_config_arg: Optional[Dict[str, str]] = None  #
) -> typer.Typer:
    """Create the command line interface of the Docker Wrapper

    Args:
        image_dir (Optional[str], optional): Directory where the Docker image Dockerfiles and
            related code are located. Defaults to None.
        env_config_arg (Optional[Dict[str, str]], optional): Configuration environment of
            the repository. Dictionary containing environment configuration values.

    Returns:
        typer.Typer: Typer class wit the registered command line arguments. See the main()
        function how an object can be instantiated.
    """
    app = typer.Typer()

    # Initialize the environment configuration based on passed argument
    # Yet expect that the environment configuration could be ovewritten
    # past the creation state. For this reason use the get_env_config() function
    # to get the configuration at execution of each subcommand.
    env_config = env_config_arg or {}
    set_env_config(env_config)

    images = {}
    if image_dir:
        global __WRAPPER_EXTENSIONS
        __WRAPPER_EXTENSIONS = find_extensions(Path(image_dir))
        images = {i: i for i in __WRAPPER_EXTENSIONS.keys()}
        global __DOCKER_IMAGE_CLASS_NAME
        image_names = Enum(__DOCKER_IMAGE_CLASS_NAME, images)  # type: ignore
    else:
        image_names = str  # type: ignore

    @app.callback()
    def main(
        image_dir: Path = typer.Option(image_dir, help="Path where the docker images are located"),
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
        global __WRAPPER_EXTENSIONS
        __WRAPPER_EXTENSIONS = find_extensions(image_dir)

        docker_login_cmd = get_env_config().get("docker_login_command", "")

        if docker_login_cmd:
            logging.info("Performing docker login")
            subprocess.run(docker_login_cmd, shell=True, check=True)

    @app.command()
    def build(
        image_name: image_names,
    ) -> None:
        """Build a docker image

        Args:
            image_name (image_names): Name of the image to build
        """
        env_config = get_env_config()
        image = __create_image(__get_image_name_value(image_name), **env_config)  # type: ignore
        image.build_image()

    @app.command()
    def push(
        image_name: image_names,
    ) -> None:
        """Push a Docker image to a Docker registry

        Args:
            image_name (image_names): Name of the image to push
        """
        env_config = get_env_config()
        image = __create_image(__get_image_name_value(image_name), **env_config)  # type: ignore
        image.push()

    @app.command()
    def pull(
        image_name: image_names,
    ) -> None:
        """Pull a docker image form a Docker registry

        Args:
            image_name (image_names): Name of the image to pull
        """
        env_config = get_env_config()
        image = __create_image(__get_image_name_value(image_name), **env_config)  # type: ignore
        image.pull()

    @app.command()
    def image_url(
        image_name: image_names,
    ) -> None:
        """URL of the image to use

        Args:
            image_name (image_names): Name of the image to pull
        """
        env_config = get_env_config()
        image = __create_image(__get_image_name_value(image_name), **env_config)  # type: ignore
        print(image.image_url)

    @app.command()
    def prompt(
        image_name: image_names,
        project_dir: Path = typer.Option(".", help="Path of the repo top-level"),
        network: Optional[str] = typer.Option(None, help="Pass the network information."),
        privileged: bool = typer.Option(False, help="Enable Docker privileged mode"),
        ports: Optional[List[str]] = typer.Option(None, help="Port to forward from Docker"),
        volume: Optional[List[str]] = typer.Option(None, help="Volume to mount"),
        sudo: bool = typer.Option(True, help="Enable sudo inside the container"),
    ) -> None:
        """
        Prompt subcommand, start a docker container and drop the user inside a prompt

        """
        env_config = get_env_config()
        image = __create_image(__get_image_name_value(image_name), **env_config)  # type: ignore
        image.run(
            prompt=True,
            project_dir=project_dir,
            network=network,
            privileged=privileged,
            ports=ports,
            volumes=volume,
            enable_sudo=sudo,
        )

    @app.command()
    def run(
        image_name: image_names,
        arguments: List[str],
        project_dir: Path = typer.Option(".", help="Path of the repo top-level"),
        privileged: bool = typer.Option(False, help="Enable Docker privileged mode"),
        ports: Optional[List[str]] = typer.Option(None, help="Port to forward from Docker"),
        volume: Optional[List[str]] = typer.Option(None, help="Volume to mount"),
        sudo: bool = typer.Option(True, help="Enable sudo inside the container"),
    ) -> None:
        """Run the following command inside the container"""
        env_config = get_env_config()
        image = __create_image(__get_image_name_value(image_name), **env_config)  # type: ignore
        image.run(
            cmds=arguments,
            project_dir=project_dir,
            privileged=privileged,
            ports=ports,
            volumes=volume,
            enable_sudo=sudo,
        )

    for k in images.keys():

        @app.command(k)
        def run_image(
            arguments: List[str],
            project_dir: Path = typer.Option(".", help="Path of the repo top-level"),
            privileged: bool = typer.Option(False, help="Enable Docker privileged mode"),
            ports: Optional[List[str]] = typer.Option(None, help="Port to forward from Docker"),
            volume: Optional[List[str]] = typer.Option(None, help="Volume to mount"),
            name: str = k,
        ) -> None:
            env_config = get_env_config()
            image = __create_image(__get_image_name_value(name), **env_config)  # type: ignore
            image.run(
                cmds=arguments,
                project_dir=project_dir,
                privileged=privileged,
                ports=ports,
                volumes=volume,
            )

    return app


def main() -> None:
    """Helper main function"""
    app = create_cli()
    app()


# Allow the script to be run standalone (useful during development).
if __name__ == "__main__":
    main()
