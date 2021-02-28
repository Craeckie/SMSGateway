import asyncio
from datetime import datetime

from nio import MatrixRoom, Event, RoomMessageText, RoomMessageImage

from smsgateway import sink_sms
from smsgateway.sources.matrix_utils import init_client
from smsgateway.sources.utils import *

IDENTIFIER = "MX"

app_log = setup_logging("matrix")


async def message_callback(room: MatrixRoom, event: Event) -> None:
    if not isinstance(event, RoomMessageText):
        app_log.debug(str(event))
    if type == 'm.room.encrypted' and event.decrypted == False:
        return

    if isinstance(event, RoomMessageText) or isinstance(event, RoomMessageImage):
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
            'ID': event.event_id,
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
                to_user = [user for u_id, user in room.users.items() if u_id != event.sender][0]
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

        text = event.body
        if isinstance(event, RoomMessageImage):
            text += ' (Picture)'
        #if event.
        #chat_info['edit']
        sink_sms.send_dict(IDENTIFIER, event.body, chat_info)


async def main() -> None:
    client = await init_client()

    # Trust all devices
    #dev_response = await client.devices()
    #print(dev_response.devices)
    # for device in dev_response.devices:
    #     print("Trusting device " + device.display_name)
    #     client.verify_device(device)


    client.add_event_callback(message_callback, Event)

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


print("Listening to messages..")
asyncio.get_event_loop().run_until_complete(main())
