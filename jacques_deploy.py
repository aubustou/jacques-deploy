import json
import logging
import subprocess
import time
from argparse import ArgumentParser
from dataclasses import InitVar, dataclass, field
from pathlib import Path

logging.basicConfig(level=logging.INFO)
INSTALLATION_PATH = Path("/opt/jacques/installation")
GIT_CLONE_PATH = Path("/opt/jacques/git")


@dataclass
class WatcherConfig:
    name: str

    exec_name: str

    # Repository config
    git_address: str
    git_branch: str

    # Python config
    python_exec_path: str = "python3"

    force_reinstall: bool = False

    venv_path: Path = field(init=False)
    bin_path: Path = field(init=False)
    pip_exec: str = field(init=False)
    service_exec: str = field(init=False)
    git_path: Path = field(init=False)

    def __post_init__(self):
        self.installation_path = INSTALLATION_PATH / self.name

        self.bin_path = self.installation_path / "venv" / "bin"
        self.pip_exec = str(self.bin_path / "pip")
        self.service_exec = str(self.bin_path / self.exec_name)
        self.git_path = GIT_CLONE_PATH / self.name

        Path(self.installation_path).mkdir(parents=True, exist_ok=True)


def get_config(config_file: Path):
    with open(config_file) as f:
        return WatcherConfig(**json.load(f))


def create_systemd_service(name: str, path: str) -> list[str]:
    cmd = [
        "systemd-run",
        f"--unit=jacques-{name}.service",
        path,
    ]
    logging.info("Creating systemd service: %s", " ".join(cmd))

    return cmd


def restart_systemd_service(name: str):
    logging.info("Restarting systemd service: %s", name)
    subprocess.run(["systemctl", "restart", f"jacques-{name}.service"], check=True)


def stop_service(name: str):
    logging.info("Stopping systemd service: %s", name)
    subprocess.run(["systemctl", "stop", f"jacques-{name}.service"], check=True)


def check_git_repo(path: Path):
    if not path.is_dir():
        raise ValueError(f"{path} is not a directory")

    if not path.joinpath(".git").is_dir():
        raise ValueError(f"{path} is not a git repository")


def install_package(config: WatcherConfig):
    logging.info("Installing package %s", config.name)
    subprocess.run(
        [
            config.pip_exec,
            "install",
            "--upgrade",
            "--force-reinstall" if config.force_reinstall else "",
            str(config.git_path / "."),
        ],
        cwd=config.git_path,
        check=True,
    )


def install_venv(config: WatcherConfig):
    logging.info("Installing venv")
    subprocess.run(
        [config.python_exec_path, "-m", "venv", "venv"],
        cwd=config.installation_path,
        check=True,
    )

    logging.info("Upgrading pip, setuptools, wheel")
    subprocess.run(
        [config.pip_exec, "install", "--upgrade", "pip", "setuptools", "wheel"],
        check=True,
    )

    install_package(config)


def setup(config: WatcherConfig):
    logging.info("Setting up jacques")

    if not config.git_path.exists():
        logging.info("Cloning git repository")
        subprocess.run(
            ["git", "clone", config.git_address, config.git_path], check=True
        )

    if not Path(config.service_exec).exists():
        install_venv(config)

    cmd = create_systemd_service(config.name, config.service_exec)
    subprocess.run(cmd, check=True)


def get_local_head(config: WatcherConfig) -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=config.git_path)
        .decode()
        .strip()
    )


def get_remote_head(config: WatcherConfig) -> str:
    return (
        subprocess.check_output(
            ["git", "ls-remote", "origin", config.git_branch], cwd=config.git_path
        )
        .decode()
        .split()[0]
    )


def git_pull(config: WatcherConfig):
    logging.info("Pulling git repository")
    subprocess.run(["git", "pull"], cwd=config.git_path, check=True)


def loop(config: WatcherConfig):
    while True:
        if get_local_head(config) != get_remote_head(config):
            git_pull(config)
            install_package(config)
            restart_systemd_service(config.name)
        time.sleep(30)


def main():
    parser = ArgumentParser(prog="jacques_deploy.py", description="Deploy jacques")
    parser.add_argument(
        "--config", help="Path to config file", type=Path, default="config.json"
    )

    INSTALLATION_PATH.mkdir(parents=True, exist_ok=True)
    GIT_CLONE_PATH.mkdir(parents=True, exist_ok=True)

    args = parser.parse_args()
    config = get_config(args.config)

    setup(config)
    try:
        loop(config)
    finally:
        stop_service(config.name)
        logging.info("Cleaning up jacques")


if __name__ == "__main__":
    main()
