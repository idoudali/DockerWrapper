#!/usr/bin/env python3
"""Helpers for building, pulling, pushing, and running Docker images."""

import getpass
import logging
import os
from pathlib import Path
import subprocess
import sys

import checksumdir
import docker


class DockerImage:
    """Interface for building and running a Docker image."""

    NAME = "UNDEFINED"

    def __init__(self, docker_registry_prefix: str = "", **kwargs: int) -> None:
        """Initialize the DockerImage object.

        Args:
            docker_registry_prefix (str, optional): The prefix of the Docker registry URL.
                Defaults to "".
            **kwargs: Additional keyword arguments.
        """
        self.docker_client = docker.from_env()
        self.name = "UNDEFINED"
        self.docker_folder = ""
        self.version = ""
        self.repo_url = docker_registry_prefix or None

    @staticmethod
    def _exec_cmd(cmd: list[str]) -> None:
        """Execute a shell command and log it.

        Args:
            cmd (list[str]): The command and its arguments in a list format.
        """
        logging.info(" ".join(cmd))
        subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)  # noqa: S603

    @staticmethod
    def folder_hash(docker_path: str) -> str:
        """Return a SHA1 hash of the Docker folder contents.

        Args:
            docker_path (str): Path of the Docker folder that contains the Dockerfile
                the entrypoint and any other related logic.

        Returns:
            str: Return the hash of the contents of the Docker folder.
        """
        return checksumdir.dirhash(docker_path, "sha1")

    @property
    def image_hash(self) -> str:
        """Return the full hash of the image.

        Returns:
            str: Hash value.
        """
        return self.folder_hash(self.docker_folder)

    @property
    def image_tag(self) -> str:
        """Return the tag of the image.

        If the image has an explicit numeric version return that, else
        return the first 10 characters of the image hash.

        Returns:
            str: Return string to be used at the image tag.
        """
        if self.version:
            return self.version
        return self.image_hash[:10]

    @property
    def tagged_name(self) -> str:
        """Return the tuple <IMAGE_NAME>:<IMAGE_TAG>.

        Returns:
            str: String result
        """
        return f"{self.name}:{self.image_tag}"

    @property
    def image_url(self) -> str:
        """Return the full image URL.

        Format is ``<REPO_URL>/<IMAGE_NAME>:<IMAGE_TAG>``.

        Returns:
            str: String result
        """
        if not self.repo_url:
            return self.tagged_name
        return f"{self.repo_url}/{self.tagged_name}"

    def build_image(self, force_build: bool = False) -> None:
        """Build the Docker image unless that version already exists.

        Args:
            force_build: If True, rebuild even when the tagged image exists.
        """
        image_url = self.image_url
        if self.image_exists(image_url) and not force_build:
            logging.info(f"Image: {image_url} already exists, not rebuilding")
            return
        cmd = ["docker", "build", self.docker_folder, "-t", image_url]
        self._exec_cmd(cmd)

    def pull(self) -> None:
        """Pull the image from the registry."""
        cmd = ["docker", "pull", self.image_url]
        self._exec_cmd(cmd)

    def push(self) -> None:
        """Push the image to the registry."""
        cmd = ["docker", "push", self.image_url]
        self._exec_cmd(cmd)

    def image_exists(self, url: str) -> bool:
        """Return true if a docker image exists locally.

        Args:
            url (str): Full URL:TAG name of the image

        Returns:
            bool: True iff the image exists locally
        """
        try:
            self.docker_client.images.get(url)
            return True
        except docker.errors.ImageNotFound:
            return False

    def get_docker_run_args(self) -> list[str]:
        """Return the list of additional arguments to pass to the docker run command.

        This function should be overridden by the child classes to provide
        the necessary arguments.
        """
        return []

    def run(
        self,
        project_dir: Path,
        prompt: bool = False,
        mount_home: bool = False,
        cmds: list[str] | None = None,
        network: str | None = None,
        privileged: bool = False,
        enable_gui: bool = False,
        ports: list[str] | None = None,
        volumes: list[str] | None = None,
        envs: list[str] | None = None,
        enable_sudo: bool = False,
        mount_host_passwd: bool = True,
    ) -> None:
        """Run a container from the Docker Image.

        Args:
            project_dir (Path): Project we want to work inside the container.
                Mount the volume inside the container
            prompt (bool, optional): Iff true start the container in interactive mode and
                start a prompt to provide to the user. Defaults to False.
            mount_home: If True, mount the host home directory into the container.
            cmds (Optional[List[str]], optional): List of commands to run inside the container.
                Defaults to None.
            network (Optional[str], optional): Name of the network to connect the container to.
                Defaults to None.
            privileged (bool, optional): Enable privileged mode. Defaults to False.
            enable_gui (bool, optional): Enable support for starting GUI apps inside the container.
                Defaults to False.
            ports (Optional[List[str]], optional): List of ports to enable to open from the
                container. Defaults to None.
            volumes (Optional[List[str]], optional): List of volumes to mount inside the container.
            envs: Environment variables to pass to the container as KEY=VALUE strings.
            enable_sudo (bool, optional): Enable sudo inside the container. Defaults to False. This
                option mounts the sudoers file inside the container.
            mount_host_passwd (bool, optional): Mount the host passwd related files inside the
                container and make use of the `-u` Docker option to map the user to the host user.
        """
        if not (bool(prompt) ^ bool(cmds)):
            raise RuntimeError("Either or neither prompt or cmds are set, only one could be set")
        image_url = self.image_url
        logging.debug(f"Using Image: {image_url}")
        if not self.image_exists(image_url):
            logging.debug(f"Image {image_url} does not exist")
            self.build_image()
        uid = os.getuid()
        gid = os.getgid()
        username = getpass.getuser()
        logging.debug(f"uid:{uid}, gid:{gid}, username:{username}")
        home_dir = os.path.expanduser("~")
        cmd = ["docker"]
        cmd += ["run", "--rm", "--hostname=Docker"]
        project_realpath = os.path.realpath(project_dir)
        if privileged:
            cmd += ["--privileged"]
        if enable_gui:
            cmd += [
                "-e",
                "DISPLAY=$DISPLAY",
                "-v",
                "/tmp/.X11-unix:/tmp/.X11-unix",  # noqa: S108
            ]
        if volumes:
            for v in volumes:
                cmd += ["-v", v]
        if network:
            cmd += [f"--network={network}"]
        if mount_host_passwd:
            cmd += [
                "-v",
                "/etc/group:/etc/group:ro",
                "-v",
                "/etc/passwd:/etc/passwd:ro",
                "-v",
                "/etc/shadow:/etc/shadow:ro",
                "-u",
                f"{uid}:{gid}",
            ]

            # Enable sudo only if we are mounting host password files
            if enable_sudo:
                cmd += ["-v", "/etc/sudoers.d:/etc/sudoers.d:ro"]

        cmd += [
            "-e",
            f"SRC_DIR={project_realpath}",
        ]
        if ports:
            for port in ports:
                cmd += ["-p", f"{port}:{port}"]

        if prompt:
            cmd += ["-t", "-i", "-e", "PROMPT=1"]

        cmd += self.get_docker_run_args()
        if mount_home:
            cmd += [
                "-v",
                home_dir + ":" + home_dir,
            ]
        if envs:
            for env in envs:
                cmd += ["-e", env]
        cmd += [
            "-v",
            f"{project_realpath}:{project_realpath}",
            image_url,
        ]

        if cmds:
            cmd.append(" ".join(cmds))

        self._exec_cmd(cmd)
