"""ubuntu_base docker image."""

import os

import docker_wrapper


class UbuntuBase(docker_wrapper.DockerImage):
    """ubuntu_base docker image.

    Args:
        docker_wrapper (_type_): Parent class
    """

    NAME = "ubuntu_base"

    def __init__(self, **kwargs) -> None:
        """Initialize the ubuntu_base image metadata.

        Args:
            **kwargs: Extra configuration forwarded to ``DockerImage``.
        """
        super().__init__(**kwargs)
        self.name = UbuntuBase.NAME
        self.docker_folder = os.path.realpath(
            os.path.join(os.path.realpath(__file__), "../Docker")
        )
        print(self.docker_folder)

    def get_docker_run_args(self) -> list[str]:
        """Return extra ``docker run`` arguments for this image."""
        return ["--network", "host"]
