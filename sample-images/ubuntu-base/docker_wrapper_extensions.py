"""Extensions to docker_wrapper for this project"""

import os
from typing import List

import docker_wrapper


class DockerImage(docker_wrapper.DockerImage):
    def __init__(self) -> None:
        super().__init__()
        self.name = "ubuntu-base"
        self.docker_folder = os.path.realpath(
            os.path.join(os.path.realpath(__file__), "../Docker")
        )
        print(self.docker_folder)

    def get_docker_run_args(self) -> List[str]:
        """"""
        return ["--network", "host"]
