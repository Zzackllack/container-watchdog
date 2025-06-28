import time
import requests
import yaml

def load_config(path='config/config.yaml'):
    """
    Loads the configuration from a YAML file.
    We use safe_load to avoid untrusted code execution.
    """
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def log(msg):
    """Simple timestamped console logger in german format"""
    print(f"[{time.strftime('%d-%m-%Y %H:%M:%S')}] {msg}")


def restart_container(config):
    """
    Executes the restart behavior defined in config:
      - "restart": direct API restart
      - "stop_start": stop then start with optional delay
    """
    api_url     = config['portainer']['url']
    api_key     = config['portainer']['api_key']
    endpoint_id = config['portainer']['endpoint_id']
    container   = config['container']['name']
    behavior    = config.get('restart', {}).get('behavior', 'restart')
    delay       = config.get('restart', {}).get('delay', 5)

    headers = {'X-API-Key': api_key}

    if behavior == 'stop_start':
        log(f"[INFO] Stopping container '{container}' via API...")
        url_stop = f"{api_url}/api/endpoints/{endpoint_id}/docker/containers/{container}/stop"
        r1 = requests.post(url_stop, headers=headers)
        log(f"[INFO] Stop response: {r1.status_code}")

        log(f"[INFO] Waiting {delay}s before starting container...")
        time.sleep(delay)

        log(f"[INFO] Starting container '{container}' via API...")
        url_start = f"{api_url}/api/endpoints/{endpoint_id}/docker/containers/{container}/start"
        r2 = requests.post(url_start, headers=headers)
        log(f"[INFO] Start response: {r2.status_code}")

        if r1.status_code in (204, 304) and r2.status_code in (204, 304):
            log(f"[INFO] Container '{container}' stopped and started successfully.")
        else:
            log(f"[ERROR] Error during stop/start sequence: stop={r1.status_code}, start={r2.status_code}")

    else:
        # default: direct restart
        log(f"[INFO] Restarting container '{container}' via API...")
        url = f"{api_url}/api/endpoints/{endpoint_id}/docker/containers/{container}/restart"
        r = requests.post(url, headers=headers)
        log(f"[INFO] Restart response: {r.status_code}")

        if r.status_code == 204:
            log(f"[INFO] Container '{container}' was restarted successfully.")
        else:
            log(f"[ERROR] Restart failed with {r.status_code}: {r.text}")


def check_sites(config):
    """
    Checks the URLs specified in the config and determines if an error status is present.
    Returns True if an error was found (restart required), otherwise False.
    """
    urls = config.get('checks', {}).get('urls', [])
    error_codes = config.get('checks', {}).get('error_status_codes', [])
    for url in urls:
        log(f"Checking {url}...")
        try:
            resp = requests.head(url, timeout=5)
            status = resp.status_code
        except requests.RequestException as e:
            log(f"[ERROR] {url} could not be reached: {e}")
            return True
        if status in error_codes:
            log(f"[ERROR] {url} returned status code {status}")
            return True
        else:
            log(f"[OK] {url} returned status code {status}")
    return False


if __name__ == "__main__":
    cfg = load_config()
    log("Loaded configuration.")
    log("Checking configured URLs...")

    if check_sites(cfg):
        log("Error detected in health checks. Proceeding to restart...")
        restart_container(cfg)
    else:
        log("All URLs OK. No restart required.")