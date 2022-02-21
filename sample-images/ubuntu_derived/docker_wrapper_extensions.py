"""Extensions to docker_wrapper for this project"""

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
    def __init__(self) -> None:
        super().__init__()
        self.parent = parent_image.DockerImage()
        self.name = "ubuntu_derived"
        self.docker_folder = os.path.realpath(
            os.path.join(os.path.realpath(__file__), "../Docker")
        )

    @property
    def image_hash(self) -> str:
        parent_image_hash = self.parent.image_hash
        logging.debug(f"Parent hash: {parent_image_hash}")
        this_image_hash = self.folder_hash(self.docker_folder)
        logging.debug(f"This image hash {this_image_hash}")
        hash_object = hashlib.sha1(
            parent_image_hash.encode("utf8") + this_image_hash.encode("utf8")
        ).hexdigest()
        return hash_object

    def build_image(self, force_build: bool = False) -> None:
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
