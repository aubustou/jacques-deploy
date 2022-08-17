# jacques-deploy

Automatized tool for remote deployment of Python services

## Features

- Allow for remote deployment on servers through only Git access
- Run remotely installed services as systemd services
- Listen for changes on Git repository and install the latest version from the branch you specified
- Remote installation supports all Python 3 versions
- No weird dependencies, only standard Python

## Configuration

Watchers are configured with help of a `config.json` file:
```json
{
  "name": "<name of the service>",
  "exec_name": "<name of the executable>",
  "git_address": "<address to the remote Git repository>",
  "git_branch": "<branch you want to lookup>",
  "python_exec_path": "<Python executable>"
}
```

## Installation

```bash
git clone https://github.com/aubustou/jacques-deploy.git
cd jacques-deploy && python3.9 -m venv venv && venv/bin/python -m pip install .
```

Launch jacques-deploy as root with 
```bash
sudo venv/bin/jacques-deploy --config <PATH_TO_CONFIG>
```
systemd unit name is `jacques-<name of the name in configuration file>.service`.

## Launch options

- `--config` sets the path to the JSON configuration file


## Where are my venv and git repositories located?
They can be found in `/opt/jacques`. Venv folders are in `installation` folder and git repositories in `git` folder`.
