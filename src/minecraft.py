"""
minecraft.py
Parse incoming websocket data from minecraft to build out the
messages and events we want to detect to send back to the
websocket for display on minecraft servers and to discord.
"""

from datetime import datetime
from src.debug import DEBUG_MODE
from src.broadcast import broadcast_to_all
import src.regexes


def parse_output(output, server):
    """
    Parse the websocket output into something we can use
    """
    try:
        print((None, f"[{server['external_id']}] {output}")[DEBUG_MODE])

        server_name = server.get('external_id').lower()

        # Make sure 'server' is a dictionary with the right key
        if (not isinstance(server, dict)
                or 'external_id' not in server
                or not isinstance(server.get('external_id'),
                                  str)):
            print(
                (None, f"[ERROR] Invalid server object passed to parse_output: {server!r}")
                [DEBUG_MODE]
            )
            raise TypeError(f"[ERROR] Invalid server object passed to parse_output: {server!r}")

        if not server_name:
            print(
                (None, "[ERROR] Server external_id missing. Did you assign one in Pelican?")
                [DEBUG_MODE]
            )
            raise TypeError("[ERROR] Server external_id missing. Did you assign one in Pelican?")

        # Get the regex dictionary for this server
        server_regexes = getattr(src.regexes, server_name, None)
        if not server_regexes:
            print((None, f"No regexes found for server: {server_name}")[DEBUG_MODE])
            raise ValueError(f"No regexes found for server: {server_name}")

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
                            return build_chat_message(server_name, server, time, user, message)
                        case "join":
                            return build_event(
                                'join', server_name, server, time, user,
                                "joined the server."
                            )
                        case "part":
                            return build_event(
                                'part', server_name, server, time, user,
                                "left the server."
                            )
                        case "ban":
                            return build_event(
                                'ban', server_name, server, time, user,
                                "was banned from the server."
                            )
                        case "pardon":
                            return build_event(
                                'ban', server_name, server, time, user,
                                "was unbanned from the server."
                            )
                        case "advancement":
                            return build_event('advancement', server_name, server, time, user, advancement)
                        case _:
                            print("[ERROR] Unexpected message in bagging area.")
                else:
                    # Server name in the log line didn't match this server, ignore match
                    continue
    except TypeError as e:
        print(e)
    except ValueError as e:
        print(e)


def time_cvt(time) -> str:
    """
    Convert 24-hour time into 12-hour time.
    """
    try:
        t = datetime.strptime(time, "%H:%M:%S")
        return t.strftime("%I:%M%p")
    except ValueError:
        return time


def build_chat_message(server, origin, time, user, message) -> str:
    """
    Build the message for a chat event.
    """
    data = (f'tellraw @a ['
            f'{{"text":"[{server}] ","color":"red"}},'
            f'{{"text":"<{user}> ","color":"blue"}},'
            f'{{"text":"{message}","color":"white"}}]\n'
            )
    broadcast_to_all(origin, data, except_origin=True)
    print((None, f"[{server}] [{time}] <{user}> {message}")[DEBUG_MODE])
    return f"[{server}] [{time}] <{user}> {message}"


def build_event(event_type, server, origin, time, user, event) -> str:
    """
    Build the message for an Event event.
    """
    match event_type:
        case 'advancement':
            data = (f'tellraw @a ['
                    f'{{"text":"[mc:{server}] ","color":"red"}},'
                    f'{{"text":"{user} made the advancement: ","color":"blue"}},'
                    f'{{"text":"{event}","color":"yellow"}}]\n')
            broadcast_to_all(origin, data, except_origin=True)
            print((None, f"[{server}] [{time}] {user} got the advancement {event}!")[DEBUG_MODE])
            return f"[{server}] [{time}] {user} got the advancement {event}!"
        case _:
            print((None, f"[{server}] [{time}] {user} {event}")[DEBUG_MODE])
            return f"[{server}] [{time}] {user} got the advancement {event}!"
