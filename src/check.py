import requests
import yaml

def load_config(path='config/config.yaml'):
    """
    Loads the configuration from a YAML file.
    We use safe_load to avoid untrusted code execution.
    """
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def restart_container(config):
    """
    Executes the restart via the Portainer API.
    """
    api_url     = config['portainer']['url']
    api_key     = config['portainer']['api_key']
    endpoint_id = config['portainer']['endpoint_id']
    container   = config['container']['name']

    headers = {
        'X-API-Key': api_key
    }

    # Restart endpoint (Portainer as gateway to the Docker Engine API)
    url = f"{api_url}/api/endpoints/{endpoint_id}/docker/containers/{container}/restart"
    response = requests.post(url, headers=headers)
    # HTTP status 204 = No Content: successful restart
    if response.status_code == 204:
        print(f"[OK] Container '{container}' was restarted.")
    else:
        print(f"[ERROR] Restart failed: {response.status_code} {response.text}")


# New function to check the sites
def check_sites(config):
    """
    Checks the URLs specified in the config and determines if an error status is present.
    Returns True if an error was found (restart required), otherwise False.
    """
    urls = config.get('checks', {}).get('urls', [])
    error_codes = config.get('checks', {}).get('error_status_codes', [])
    for url in urls:
        try:
            resp = requests.head(url, timeout=5)
            status = resp.status_code
        except requests.RequestException as e:
            print(f"[ERROR] {url} could not be reached: {e}")
            return True
        if status in error_codes:
            print(f"[ERROR] {url} returned status code {status}")
            return True
        else:
            print(f"[OK] {url} returned status code {status}")
    return False

if __name__ == "__main__":
    cfg = load_config()
    if check_sites(cfg):
        restart_container(cfg)
    else:
        print("All URLs OK, no restart required.")