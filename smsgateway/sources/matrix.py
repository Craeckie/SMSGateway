import asyncio, json, os, sys, getpass
import time
from datetime import datetime

from nio import AsyncClient, LoginResponse

from smsgateway import sink_sms
from smsgateway.sources.utils import *
from smsgateway.config import *

from nio import AsyncClient, MatrixRoom, RoomMessageText

CONFIG_DIR = user_config_dir(appname="smsgateway", appauthor="craeckie")
CONFIG_FILE = os.path.join(CONFIG_DIR, "matrix-token.json")

IDENTIFIER = "MX"
User = None

async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    print(
        f"Message received in room {room.display_name}\n"
        f"{room.user_name(event.sender)} | {event.body}"
    )
    chat_info = {
        'ID': event.server_timestamp,
        'date': datetime.utcfromtimestamp(event.server_timestamp / 1000),
        'type': 'Group' if room.is_group else 'User'
    }
    if event.sender == User:  # I sent this message
        if room.is_group or len(room.users) == 1:
            chat_info.update({
                'to_id': room.room_id,
                'to': room.name
            })
        else:
            to_id = list(filter(lambda u: u != User, room.users))[0]
            to_user = room.users[to_id]
            chat_info.update({
                'to_id': to_user.user_id,
                'to': to_user.display_name
            })

    else:
        from_id = list(filter(lambda u: u != User, room.users))[0]
        from_user = room.users[from_id]
        chat_info.update({
            'from_id': from_user.user_id,
            'from': from_user.display_name
        })
        if room.is_group:
            chat_info.update({
                'to_id': room.room_id,
                'to': room.name
            })
    #if event.
    #chat_info['edit']
    sink_sms.send_dict(IDENTIFIER, event.body, chat_info)


async def main() -> None:
    global MATRIX_HS_URL, User
    client = None
    # If there are no previously-saved credentials, we'll use the password
    if not os.path.exists(CONFIG_FILE):
        print("First time use. Did not find credential file. Asking for "
              "homeserver, user, and password to create credential file.")
        if not (MATRIX_HS_URL.startswith("https://")
                or MATRIX_HS_URL.startswith("http://")):
            MATRIX_HS_URL = "https://" + MATRIX_HS_URL

        User, Pass = MATRIX_CREDENTIALS
        client = AsyncClient(MATRIX_HS_URL, User)

        device_name = "SMSGateway"

        resp = await client.login(Pass, device_name=device_name)

        if (isinstance(resp, LoginResponse)):
            write_details_to_disk(resp, MATRIX_HS_URL)
        else:
            print(f"homeserver = \"{MATRIX_HS_URL}\"; user = \"{User}\"")
            print(f"Failed to log in: {resp}")
            sys.exit(1)

    # Otherwise the config file exists, so we'll use the stored credentials
    else:
        # open the file in read-only mode
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            client = AsyncClient(config['homeserver'])

            client.access_token = config['access_token']
            client.user_id = config['user_id']
            client.device_id = config['device_id']

    # If you made a new room and haven't joined as that user, you can use
    # await client.join("your-room-id")

    client.add_event_callback(message_callback, RoomMessageText)

    await client.room_send(
        # Watch out! If you join an old room you'll see lots of old messages
        room_id="!hBplPMIfOEdWDvufsV:matrix.sanemind.de",
        message_type="m.room.message",
        content={
            "msgtype": "m.text",
            "body": "Hello world!"
        }
    )
    await client.sync_forever()

def write_details_to_disk(resp: LoginResponse, homeserver) -> None:
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
                "access_token": resp.access_token  # cryptogr. access token
            },
            f
        )



asyncio.get_event_loop().run_until_complete(main())
