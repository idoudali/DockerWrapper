#!/usr/bin/env python3
import argparse
import argcomplete
import importlib
import importlib.util
import checksumdir
import docker
import logging
import os
import getpass
import subprocess
import sys

_LOG_LEVEL_STRINGS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

DOCKER_FOLDERS = [
    os.path.realpath(os.path.join(root, dir))
    for root, dirs, files in os.walk(os.getcwd(), topdown=True) for dir in dirs
    if 'Docker' == dir
]

FOLDERS = [
    os.path.realpath(os.path.join(i, '..')) for i in DOCKER_FOLDERS
    if os.path.exists(os.path.join(i, '../docker_wrapper_extensions.py'))
]

WRAPPER_EXTENSIONS = {}

for f in FOLDERS:
    spec = importlib.util.spec_from_file_location(
        "docker_wrapper_extensions",
        os.path.join(f, 'docker_wrapper_extensions.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    name = os.path.split(f)[1]
    WRAPPER_EXTENSIONS[name] = (f, mod)


def image_hash(docker_file_path):
    """Compute the hash  of the docker image based on the
    contents of the Docker folder of the project

    Return  the 10 first digits"""
    return checksumdir.dirhash(docker_file_path, 'sha1')[:10]


def build_image(docker_client, image_name, tag, docker_file_path):
    """Build the image"""
    cmd = [
        'docker', 'build', docker_file_path, '-t',
        "{}:{}".format(image_name, tag)
    ]
    print(cmd)
    subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)


def image_exists(docker_client, image_name, tag):
    """Return true if a docker image exists"""
    try:
        docker_client.images.get("{}:{}".format(image_name, tag))
        return True
    except docker.errors.ImageNotFound:
        return False


def run(args):
    docker_client = docker.from_env()
    project_path, extension = WRAPPER_EXTENSIONS[args.project]
    docker_folder = os.path.join(project_path, 'Docker')
    image_name = args.project.lower()
    hash = image_hash(docker_folder)
    logging.debug("Dir Hash: {}".format(hash))
    if not image_exists(docker_client, image_name, hash):
        logging.debug("Image {}:{} does not exist".format(image_name, hash))
        build_image(docker_client, image_name, hash, docker_folder)
    image = "{}:{}".format(image_name, hash)
    uid = os.getuid()
    gid = os.getgid()
    username = getpass.getuser()
    logging.debug("uid:{}, gid:{}, username:{}".format(uid, gid, username))
    home_dir = os.path.expanduser('~')
    cmd = ['nvidia-docker'] if args.enable_nvidia else ['docker']
    cmd += ['run', '--rm', '--hostname=Docker']
    if args.privileged:
        cmd += ['--privileged']
    if args.enable_gui:
        cmd += [
            '-e',
            'DISPLAY=$DISPLAY',
            '-v',
            '/tmp/.X11-unix:/tmp/.X11-unix',
        ]
    if args.network:
        cmd += [f"--network={args.network}"]
    cmd += [
        '-e', 'UID={}'.format(uid), '-e', 'GID={}'.format(gid), '-e',
        'USERNAME={}'.format(username), '-e', f'SRC_DIR={project_path}'
    ]
    if args.prompt:
        cmd += ['-t', '-i', '-e', 'PROMPT=1']
    if args.port:
        cmd += ["-p", "{}:{}".format(args.port, args.port)]
    if hasattr(extension, 'add_docker_args'):
        extension.add_docker_args(args, cmd)
    cmd += [
        '-v', home_dir + ":" + home_dir, '-v',
        f'{project_path}:{project_path}', image
    ]
    if hasattr(extension, 'add_entrypoint_args'):
        extension.add_entrypoint_args(args, cmd)
    logging.info("Running cmd: {}".format(" ".join(cmd)))
    subprocess.run(" ".join(cmd),
                   stdin=sys.stdin,
                   stdout=sys.stdout,
                   stderr=sys.stderr,
                   check=True,
                   shell=True)


def _log_level_string_to_int(log_level_string):
    if not log_level_string in _LOG_LEVEL_STRINGS:
        message = 'invalid choice: {0} (choose from {1})'.format(
            log_level_string, _LOG_LEVEL_STRINGS)
        raise argparse.ArgumentTypeError(message)
    log_level_int = getattr(logging, log_level_string, logging.INFO)
    # check the logging log_level_choices have not changed from our expected values
    assert isinstance(log_level_int, int)
    return log_level_int


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--log-level',
        default='INFO',
        dest='log_level',
        type=_log_level_string_to_int,
        nargs='?',
        help='Set the logging output level. {0}'.format(_LOG_LEVEL_STRINGS))
    parser.add_argument(
        '--prompt',
        action='store_true',
        help="Get a prompt inside the container for the project")
    parser.add_argument('--enable-nvidia',
                        action='store_true',
                        default=False,
                        help='Disable the use of nvidia-docker')
    parser.add_argument('--network',
                        default=None,
                        help="Pass through option to the "
                        "docker run network option")
    parser.add_argument('--privileged',
                        action='store_true',
                        help='Enable privileged mode')
    parser.add_argument('--enable-gui',
                        action='store_true',
                        help='Enable start gui apps')
    parser.add_argument('--port',
                        default="",
                        help='Port to forward from docker')
    subparsers = parser.add_subparsers(dest="project")
    subparsers.required = True

    for project, (_, mod) in WRAPPER_EXTENSIONS.items():
        subparser = subparsers.add_parser(project)
        if hasattr(mod, 'register_subparser'):
            mod.register_subparser(subparser)

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)

    run(args)
