import asyncio, json, os, sys, getpass
import time
from datetime import datetime

from nio import AsyncClient, LoginResponse, ClientConfig

from smsgateway import sink_sms
from smsgateway.sources.utils import *
from smsgateway.config import *

from nio import AsyncClient, MatrixRoom, RoomMessageText

CONFIG_DIR = user_config_dir(appname="smsgateway", appauthor="craeckie")
CONFIG_FILE = os.path.join(CONFIG_DIR, "matrix-token.json")
STORE_DIR = os.path.join(CONFIG_DIR, 'matrix-store')

IDENTIFIER = "MX"
User = None

app_log = setup_logging("matrix")

async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    app_log.info(
        f"Message received in room {room.display_name}\n"
        f"{room.user_name(event.sender)} | {event.body}"
    )
    is_group = len(room.users.keys()) > 2 or room.is_named

    if is_group and not room.is_named:
        room_name = ', '.join([user.display_name for id, user in room.users.items() if id != room.own_user_id])
    else:
        room_name = room.display_name

    chat_info = {
        'ID': event.server_timestamp,
        'date': datetime.utcfromtimestamp(event.server_timestamp / 1000),
        'type': 'Group' if is_group else 'User'
    }
    if event.sender == room.own_user_id:  # I sent this message
        if is_group:
            chat_info.update({
                'to_id': room.room_id,
                'to': room_name
            })
        else:
            to_id = list(filter(lambda u: u != User, room.users))[0]
            to_user = room.users[to_id]
            chat_info.update({
                'to_id': to_user.user_id,
                'to': to_user.display_name
            })

    else:
        from_user = [user for u_id, user in room.users.items() if u_id == event.sender][0]
        chat_info.update({
            'from_id': from_user.user_id,
            'from': from_user.display_name
        })
        if is_group:
            chat_info.update({
                'to_id': room.room_id,
                'to': room_name
            })
    #if event.
    #chat_info['edit']
    sink_sms.send_dict(IDENTIFIER, event.body, chat_info)


async def main() -> None:
    global MATRIX_HS_URL, User
    if STORE_DIR and not os.path.isdir(STORE_DIR):
        os.mkdir(STORE_DIR)

    client = None
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

    # If you made a new room and haven't joined as that user, you can use
    # await client.join("your-room-id")

    # Load devices & keys
    #client.load_store()
    

    
    # Trust all devices
    #dev_response = await client.devices()
    #print(dev_response.devices)
    # for device in dev_response.devices:
    #     print("Trusting device " + device.display_name)
    #     client.verify_device(device)


    client.add_event_callback(message_callback, RoomMessageText)

    # await client.room_send(
    #     # Watch out! If you join an old room you'll see lots of old messages
    #     room_id="!hBplPMIfOEdWDvufsV:matrix.sanemind.de",
    #     message_type="m.room.message",
    #     content={
    #         "msgtype": "m.text",
    #         "body": "Hello world!"
    #     }
    # )

    await client.sync_forever(full_state=True)

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



asyncio.get_event_loop().run_until_complete(main())
