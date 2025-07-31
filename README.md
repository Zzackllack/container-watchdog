# Container Watchdog

Container Watchdog is a Python-based tool designed to monitor the health of your web services and automatically restart Docker containers via Portainer or Checkmate if a service is down or returns error status codes. It is ideal for self-hosters and DevOps teams who want automated recovery for their containerized services.

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Docker](#docker)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

## Features

- Monitors multiple URLs and restarts mapped containers on failure
- Supports Portainer API for container management
- Integrates with Checkmate for advanced uptime monitoring
- Configurable error codes, timeouts, and restart behavior
- Runs as a Docker container or standalone Python script

## How It Works

1. Periodically checks the health of configured URLs.
2. If a URL returns an error status code or times out, the mapped container is restarted via Portainer API.
3. Optionally, checks Checkmate monitors and restarts containers if a monitor is down.
4. All settings are managed via a YAML config file.

## Installation

### Clone the Repository

```bash
git clone https://github.com/zzackllack/container-watchdog.git
cd container-watchdog
```

### Install Python Dependencies (if running locally)

```bash
pip install -r requirements.txt
# Or manually:
pip install requests pyyaml
```

## Configuration

Copy the example config and edit it for your environment:

```bash
cp config/example.config.yaml config/config.yaml
# Edit config/config.yaml with your Portainer and Checkmate details
```

See [`config/example.config.yaml`](config/example.config.yaml) for all available options and documentation.

## Usage

### Run Locally

```bash
python src/check.py
```

### Run with Docker Compose

1. Edit `config/config.yaml` as described above.
2. Start the watchdog:

```bash
docker compose up -d
```

## Docker

The provided `docker-compose.yaml` and `docker/Dockerfile` allow you to run the watchdog as a container. The config file is mounted read-only into the container.

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and our [Code of Conduct](CODE_OF_CONDUCT.md) before submitting issues or pull requests.

## License

This project is licensed under the BSD 3-Clause License. See the [LICENSE](LICENSE) file for details.

## Support

- Create an [issue](../../issues) for bug reports or feature requests
- Check our [security policy](SECURITY.md) for reporting vulnerabilities

## Acknowledgments

- Thanks to all contributors and the open source community.
