import os
from fbchat import Client

def login(credentials, cookie_path, bot_class):
    session_cookies = None
    if os.path.exists(cookie_path):
        with open(cookie_path, 'r') as f:
             session_cookies = f.read()

    client = bot_class(credentials[0], credentials[1], session_cookies=session_cookies)
    session_cookies = client.getSession()
    with open(cookie_path, 'w') as f:
        f.write(str(session_cookies))
        #f.write(json.dumps(session_cookies))
    return client
