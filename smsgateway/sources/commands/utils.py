import re


def parse_message(app_log, lines):
    messageStarted = False
    to_matched = None
    message = ""
    ret = {
        'success': False,
    }

    for line in lines[1:]:  # skip IDENTIFIER
        if messageStarted:
            message += f"\n{line}"
        elif not line.strip():  # empty line
            messageStarted = True
        else:
            mTo = re.match("^To: (.*)$", line)
            if mTo:
                to_matched = mTo.group(1).strip()
            else:
                app_log.warning(f"Unkown header: {line}!")

    if to_matched and message:
        ret.update({
            'success': True,
            'to': to_matched,
            'message': message,
        })
    else:
        ret['error'] = f"Couldn't match To: {to_matched} or message {message}"
    return ret
