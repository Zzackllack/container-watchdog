import time
import requests
import yaml
from pathlib import Path

def authenticate_checkmate(config):
    """
    Authenticate with Checkmate and return a JWT auth token.
    """
    url = f"{config['checkmate']['api_url']}/api/v1/auth/login"
    log(f"[INFO] Authenticating with Checkmate API at {url}...")
    payload = {
        'email': config['checkmate']['email'],
        'password': config['checkmate']['password']
    }
    resp = requests.post(url, json=payload, timeout=config['checkmate']['timeout'])
    if resp.status_code == 200:
        log("[OK] Successfully authenticated with Checkmate.")
    else:
        log(f"[ERROR] Authentication failed with status code {resp.status_code}: {resp.text}")
    resp.raise_for_status()
    token = resp.json().get('data', {}).get('token')
    if not token:
        log("[ERROR] No token received from Checkmate")
        raise RuntimeError("Failed to get auth token from Checkmate")
    return token

def load_config(path=None):
    """
    Loads the configuration from a YAML file next to the project root,
    regardless of the current working directory.
    """
    if path is None:
        base_dir = Path(__file__).resolve().parent.parent
        path = base_dir / "config" / "config.yaml"
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def log(msg):
    """Simple timestamped console logger in German date format"""
    print(f"[{time.strftime('%d-%m-%Y %H:%M:%S')}] {msg}")


def restart_container(config, container_name):
    """
    Restart the specified container using the behavior in config:
      - "restart": direct API restart
      - "stop_start": stop then start with optional delay
    """
    api_url     = config['portainer']['url']
    api_key     = config['portainer']['api_key']
    endpoint_id = config['portainer']['endpoint_id']
    behavior    = config.get('restart', {}).get('behavior', 'restart')
    delay       = config.get('restart', {}).get('delay', 5)

    headers = {'X-API-Key': api_key}

    if behavior == 'stop_start':
        log(f"[INFO] Stopping container '{container_name}' via API...")
        url_stop = f"{api_url}/api/endpoints/{endpoint_id}/docker/containers/{container_name}/stop"
        r1 = requests.post(url_stop, headers=headers)
        log(f"[INFO] Stop response for '{container_name}': {r1.status_code}")

        log(f"[INFO] Waiting {delay}s before starting container '{container_name}'...")
        time.sleep(delay)

        log(f"[INFO] Starting container '{container_name}' via API...")
        url_start = f"{api_url}/api/endpoints/{endpoint_id}/docker/containers/{container_name}/start"
        r2 = requests.post(url_start, headers=headers)
        log(f"[INFO] Start response for '{container_name}': {r2.status_code}")

        if r1.status_code < 300 and r2.status_code < 300:
            log(f"[INFO] Container '{container_name}' restarted successfully via stop/start.")
        else:
            log(f"[ERROR] Stop/start returned non-2xx codes for '{container_name}': stop={r1.status_code}, start={r2.status_code}")
            log(f"[DEBUG] Stop response body: {r1.text}")
            log(f"[DEBUG] Start response body: {r2.text}")

    else:
        log(f"[INFO] Restarting container '{container_name}' via API...")
        url = f"{api_url}/api/endpoints/{endpoint_id}/docker/containers/{container_name}/restart"
        r = requests.post(url, headers=headers)
        log(f"[INFO] Restart response for '{container_name}': {r.status_code}")

        if r.status_code < 300:
            log(f"[INFO] Container '{container_name}' restarted successfully.")
        else:
            log(f"[ERROR] Restart failed for '{container_name}': {r.status_code}")
            log(f"[DEBUG] Restart response body: {r.text}")

def check_sites(config):
    """
    Checks each URL in the config, logs redirects and timeouts.
    Returns a list of URLs that failed their checks.
    """
    mapping = config.get('checks', {}).get('mapping', {})
    error_codes = config.get('checks', {}).get('error_status_codes', [])
    timeout = config.get('checks', {}).get('timeout', 5)

    failed = []
    for url, container_name in mapping.items():
        log(f"[INFO] Checking {url} -> '{container_name}' with timeout {timeout}s...")
        try:
            resp = requests.head(url, timeout=timeout, allow_redirects=True)
        except requests.exceptions.Timeout:
            log(f"[WARN] Timeout after {timeout}s waiting for {url}. Countdown to failure...")
            for remaining in range(timeout, 0, -1):
                log(f"[WARN] {remaining}s left before marking {url} as failed...")
                time.sleep(1)
            log(f"[ERROR] No response from {url} after timeout and countdown.")
            failed.append(container_name)
            continue
        except requests.RequestException as e:
            log(f"[ERROR] {url} could not be reached: {e}")
            failed.append(container_name)
            continue

        # Log redirects
        for hist in resp.history:
            location = hist.headers.get('Location', '<unknown>')
            log(f"[INFO] Redirect for '{container_name}': {hist.status_code} {hist.url} -> {location}")

        status = resp.status_code
        log(f"[OK] Final URL for '{container_name}': {resp.url} returned status code {status}")

        if status in error_codes:
            log(f"[ERROR] {resp.url} returned error code {status}")
            failed.append(container_name)

    return failed

def check_checkmate(config):
    """
    Checks monitor status via Checkmate API and returns a list of container names for down monitors.
    """
    token = authenticate_checkmate(config)
    headers = {'Authorization': f"Bearer {token}"}
    url = f"{config['checkmate']['api_url']}/api/v1/monitors"
    resp = requests.get(url, headers=headers, timeout=config['checkmate']['timeout'])
    resp.raise_for_status()
    monitors = resp.json().get('data', [])
    failed = []
    for monitor in monitors:
        if monitor.get('status') is False:
            container = config['checkmate']['mapping'].get(monitor.get('_id'))
            if container:
                failed.append(container)
    return failed

if __name__ == "__main__":
    cfg = load_config()
    interval = cfg.get('interval', {}).get('seconds', 300)

    log("[INFO] Loaded configuration.")
    log(f"[INFO] Starting health check loop: interval set to {interval} seconds.")

    while True:
        log("[INFO] Checking configured URLs...")
        failed_containers = check_sites(cfg)
        if failed_containers:
            for container in failed_containers:
                log(f"[ERROR] Error detected for container '{container}'. Restarting...")
                restart_container(cfg, container)
        else:
            log("[OK] All URLs OK. No restart required.")

        # Checkmate monitors
        log("[INFO] Checking Checkmate monitors...")
        cm_failed = check_checkmate(cfg)
        if cm_failed:
            for container in cm_failed:
                log(f"[ERROR] Checkmate reports monitor down for '{container}'. Restarting...")
                restart_container(cfg, container)
        else:
            log("[OK] All Checkmate monitors OK. No restart required for Checkmate.")

        log(f"[INFO] Sleeping for {interval} seconds before next check.")
        time.sleep(interval)