from datetime import datetime

from src.debug import DEBUG_MODE
import src.regexes
import src.websocket
from src.broadcast import broadcast_to_all


def parse_output(output, server):
    if DEBUG_MODE:
        print(f"[{server['external_id']}] {output}")

    server_name = server.get('external_id').lower()

    if not server_name:
        print("[ERROR] Server external_id missing. Did you assign one in Pelican/Pterodactyl?")
        return False

    # Get the regex dictionary for this server
    server_regexes = getattr(src.regexes, server_name, None)
    if not server_regexes:
        print(f"No regexes found for server: {server_name}")
        return False

    for event_type, regex in server_regexes.items():
        match = regex.match(output)
        if match:
            groups = match.groupdict()
            # Check if the captured server in the line matches the expected server
            if groups.get("server", "").lower() == server_name:
                user = groups.get("user", None)
                message = groups.get("message", None)
                time = time_cvt(groups.get("time", None))
                advancement = groups.get("advancement", None)

                match event_type:
                    case "message":
                        build_chat_message(server_name, time, user, message)
                    case "join":
                        build_event('join', server_name, time, user, "joined the server.")
                    case "part":
                        build_event('part', server_name, time, user, "left the server.")
                    case "ban":
                        build_event('ban', server_name, time, user, "was banned from the server.")
                    case "pardon":
                        build_event('ban', server_name, time, user, "was unbanned from the server.")
                    case "advancement":
                        build_event('advancement', server_name, time, user, advancement)
                    case _:
                        print("[ERROR] Unexpected message in bagging area.")
            else:
                # Server name in log line didn't match this server, ignore match
                continue
    return None


def time_cvt(time):
    try:
        t = datetime.strptime(time, "%H:%M:%S")
        return t.strftime("%I:%M%p")
    except ValueError:
        return time


def build_chat_message(server, time, user, message):
    data = f'tellraw @a [{{"text":"[mc:{server}] ","color":"red"}},{{"text":"<{user}> ","color":"blue"}},{{"text":"{message}","color":"white"}}]\n'
    broadcast_to_all_except_origin(server, data, except_origin=True)
    print(f"[{server}] [{time}] <{user}> {message}")


def build_event(event_type, server, time, user, event):
    match event_type:
        case 'advancement':
            data = f'tellraw @a [{{"text":"[mc:{server}] ","color":"red"}},{{"text":"{user} made the advancement: ","color":"blue"}},{{"text":"{event}","color":"yellow"}}]\n'
            broadcast_to_all(server, data, except_origin=True)
            print(f"[{server}] [{time}] {user} got the advancement {event}!")
        case _:
            print(f"[{server}] [{time}] {user} {event}")
    return False
