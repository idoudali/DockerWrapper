import os
from pathlib import Path
from typing import Dict, Type

import pytest

import docker_wrapper
from docker_wrapper import docker_helpers


@pytest.fixture
def image_registry() -> Dict[str, Type[docker_helpers.DockerImage]]:
    # point to the sample_images directory
    test_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../sample-images")
    ext = docker_wrapper.cli.find_extensions(Path(test_path))
    return ext


def test_image_hash(image_registry) -> None:  # type: ignore
    assert "ubuntu_base" in image_registry
    image = image_registry["ubuntu_base"]()
    assert image.image_hash[:10] == "0d7a3669ae"
    assert image.tagged_name == "ubuntu_base:0d7a3669ae"


def test_image_prompt(image_registry, mocker) -> None:  # type: ignore
    assert "ubuntu_base" in image_registry
    image = image_registry["ubuntu_base"]()
    mocker.patch.object(image, "_exec_cmd", autospec=True)
    image.run("", prompt=True)
    run_args = image._exec_cmd.call_args.args[0]
    # print(run_args)
    assert image.tagged_name in run_args


def test_derived_image_hash(image_registry) -> None:  # type: ignore
    assert "ubuntu_derived" in image_registry
    image = image_registry["ubuntu_derived"]()
    assert image.image_hash[:10] == "b50e8bc0f5"
    assert image.tagged_name == "ubuntu_derived:b50e8bc0f5"
