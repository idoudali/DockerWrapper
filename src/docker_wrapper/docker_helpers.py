#!/usr/bin/env python3
import getpass
import logging
import os
from pathlib import Path
import subprocess
import sys
from typing import List, Optional

import checksumdir
import docker


class DockerImage:
    def __init__(self) -> None:
        self.docker_client = docker.from_env()
        self.name = "UNDEFINED"
        self.docker_folder = ""
        self.version = ""
        self.repo_url = ""

    @staticmethod
    def folder_hash(docker_path: str) -> str:
        """Compute the hash  of the docker image based on the
        contents of the Docker folder of the project

        Return  the 10 first digits"""
        return checksumdir.dirhash(docker_path, "sha1")[:10]

    @property
    def image_hash(self) -> str:
        return self.folder_hash(self.docker_folder)

    @property
    def image_version(self) -> str:
        if not self.version:
            return self.image_hash
        return self.version

    @property
    def tagged_name(self) -> str:
        return f"{self.name}:{self.image_version}"

    @property
    def image_url(self) -> str:
        if not self.repo_url:
            return self.tagged_name
        return f"{self.repo_url}/{self.tagged_name}"

    def build_image(self) -> None:
        """Build the image"""
        tag = self.image_hash
        cmd = ["docker", "build", self.docker_folder, "-t", "{}:{}".format(self.name, tag)]
        logging.info(cmd)
        subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)

    def pull(self) -> None:
        raise RuntimeError("Unsupported functionality")

    def push(self) -> None:
        raise RuntimeError("Unsupported functionality")

    def image_exists(self, url: str) -> bool:
        """Return true if a docker image exists"""
        try:
            self.docker_client.images.get(url)
            return True
        except docker.errors.ImageNotFound:
            return False

    def get_docker_run_args(self) -> List[str]:
        return []

    def run(
        self,
        project_dir: Path,
        prompt: bool = False,
        nvidia_docker: bool = False,
        privileged: bool = False,
        enable_gui: bool = False,
        ports: Optional[List[str]] = None,
    ) -> None:
        image_url = self.image_url
        logging.debug(f"Using Image: {image_url}")
        if not self.image_exists(image_url):
            logging.debug(f"Image {image_url} does not exist")
            self.build_image()
        uid = os.getuid()
        gid = os.getgid()
        username = getpass.getuser()
        logging.debug("uid:{}, gid:{}, username:{}".format(uid, gid, username))
        home_dir = os.path.expanduser("~")
        cmd = ["nvidia-docker"] if nvidia_docker else ["docker"]
        cmd += ["run", "--rm", "--hostname=Docker"]
        project_realpath = os.path.realpath(project_dir)
        if privileged:
            cmd += ["--privileged"]
        if enable_gui:
            cmd += [
                "-e",
                "DISPLAY=$DISPLAY",
                "-v",
                "/tmp/.X11-unix:/tmp/.X11-unix",
            ]
        # if args.network:
        #     cmd += [f"--network={args.network}"]
        cmd += [
            "-e",
            "UID={}".format(uid),
            "-e",
            "GID={}".format(gid),
            "-e",
            "USERNAME={}".format(username),
            "-e",
            f"SRC_DIR={project_realpath}",
        ]
        if prompt:
            cmd += ["-t", "-i", "-e", "PROMPT=1"]
        if ports:
            for port in ports:
                cmd += ["-p", f"{port}:{port}"]

        cmd += self.get_docker_run_args()
        cmd += [
            "-v",
            home_dir + ":" + home_dir,
            "-v",
            f"{project_realpath}:{project_realpath}",
            image_url,
        ]
        # if hasattr(extension, "add_entrypoint_args"):
        #     extension.add_entrypoint_args(args, cmd)
        logging.info("Running cmd: {}".format(" ".join(cmd)))
        subprocess.run(
            " ".join(cmd),
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
            shell=True,
        )
