import json
import os
import sys

from appdirs import user_config_dir
from nio import ClientConfig, AsyncClient, LoginResponse
from smsgateway.config import *
from smsgateway.sources.utils import *

app_log = setup_logging("matrix")

# CONFIG_DIR = user_config_dir(appname="smsgateway", appauthor="craeckie")
CONFIG_FILE = os.path.join(CONFIG_DIR, "matrix-token.json")
STORE_DIR = os.path.join(CONFIG_DIR, 'matrix-store')

async def init_client():
    if STORE_DIR and not os.path.isdir(STORE_DIR):
        os.mkdir(STORE_DIR)

    global MATRIX_HS_URL, User
    client_config = ClientConfig(store_sync_tokens=True)
    # If there are no previously-saved credentials, we'll use the password
    if not os.path.exists(CONFIG_FILE):
        app_log.info("First time use. Did not find credential file. Using supplied "
                     "homeserver, user, and password to create credential file.")
        if not (MATRIX_HS_URL.startswith("https://")
                or MATRIX_HS_URL.startswith("http://")):
            MATRIX_HS_URL = "https://" + MATRIX_HS_URL

        User, Pass = MATRIX_CREDENTIALS
        client = AsyncClient(MATRIX_HS_URL, User, config=client_config, store_path=STORE_DIR)

        device_name = "SMSGateway"

        resp = await client.login(Pass, device_name=device_name)

        if (isinstance(resp, LoginResponse)):
            write_details_to_disk(resp, MATRIX_HS_URL, STORE_DIR)
        else:
            print(f"homeserver = \"{MATRIX_HS_URL}\"; user = \"{User}\"")
            print(f"Failed to log in: {resp}")
            sys.exit(1)

    # Otherwise the config file exists, so we'll use the stored credentials
    else:
        # open the file in read-only mode
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            client = AsyncClient(config['homeserver'], config=client_config, store_path=config['store_path'])

            client.access_token = config['access_token']
            client.user_id = config['user_id']
            client.device_id = config['device_id']
    # Load devices & keys
    client.load_store()
    return client


def write_details_to_disk(resp: LoginResponse, homeserver, store_path) -> None:
    """Writes the required login details to disk so we can log in later without
    using a password.

    Arguments:
        resp {LoginResponse} -- the successful client login response.
        homeserver -- URL of homeserver, e.g. "https://matrix.example.org"
    """
    # open the config file in write-mode
    with open(CONFIG_FILE, "w") as f:
        # write the login details to disk
        json.dump(
            {
                "homeserver": homeserver,  # e.g. "https://matrix.example.org"
                "user_id": resp.user_id,  # e.g. "@user:example.org"
                "device_id": resp.device_id,  # device ID, 10 uppercase letters
                "access_token": resp.access_token,  # cryptogr. access token
                "store_path": store_path  # directory to store keys
            },
            f
        )
