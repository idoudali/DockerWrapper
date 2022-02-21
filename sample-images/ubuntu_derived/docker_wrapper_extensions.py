"""ubuntu_derived


Example of a docker image that inherits from another one, in this
case ubuntu_base
"""

import hashlib
import logging
import os
import sys
from typing import List

import docker_wrapper

# Add the parent directory to the PYTHONPATH to simplify importing the
# parent image code. We do not expect that docker images follow a python
# module code organization.
PARENT_DIRECTORY = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(PARENT_DIRECTORY)

from ubuntu_base import docker_wrapper_extensions as parent_image  # noqa: E402


class DockerImage(docker_wrapper.DockerImage):
    """DockerImage class of the ubuntu_derived image"""

    def __init__(self) -> None:
        super().__init__()
        self.parent = parent_image.DockerImage()
        self.name = "ubuntu_derived"
        self.docker_folder = os.path.realpath(
            os.path.join(os.path.realpath(__file__), "../Docker")
        )

    @property
    def image_hash(self) -> str:
        """Compute the hash of the derived image

        To capture correctly any possible changes to the
        parent image as well, the image hash is the combined
        has of the parent_image and the hash of the Docker folder
        of the derived image.

        Returns:
            str: Returned hash value
        """
        parent_image_hash = self.parent.image_hash
        logging.debug(f"Parent hash: {parent_image_hash}")
        this_image_hash = self.folder_hash(self.docker_folder)
        logging.debug(f"This image hash {this_image_hash}")
        hash_object = hashlib.sha1(
            parent_image_hash.encode("utf8") + this_image_hash.encode("utf8")
        ).hexdigest()
        return hash_object

    def build_image(self, force_build: bool = False) -> None:
        """Build the image

        The derived image will trigger a build of the parent image and
        then proceed to its own build.

        Args:
            force_build (bool, optional): _description_. Defaults to False.
        """
        image_url = self.image_url
        if self.image_exists(image_url) and not force_build:
            logging.info(f"Image: {image_url} already exists, not rebuilding")
            return
        self.parent.build_image()
        parent_url = self.parent.image_url
        cmd = [
            "docker",
            "build",
            "--build-arg",
            f"PARENT_IMAGE={parent_url}",
            self.docker_folder,
            "-t",
            image_url,
        ]
        self._exec_cmd(cmd)

    def get_docker_run_args(self) -> List[str]:
        """"""
        return ["--network", "host"]
