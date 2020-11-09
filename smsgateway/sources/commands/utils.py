import re


def parse_message(lines, app_log=None):
    messageStarted = False
    to_matched = None
    message = ""
    for line in lines[1:]:  # skip IDENTIFIER
        if messageStarted:
            if message:
                message += "\n"
            message += f"{line}"
        elif not line.strip():  # empty line
            messageStarted = True
        else:
            mTo = re.match("^To: (.*)$", line)
            if mTo:
                to_matched = mTo.group(1).strip()
            else:
                if app_log:
                    app_log.warning(f"Unkown header: {line}!")
                else:
                    print(f"Warning: Unkown header: {line}!")
    return message, to_matched
