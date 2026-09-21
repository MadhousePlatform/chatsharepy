"""
minecraft.py
Parse incoming websocket data from minecraft to build out the
messages and events we want to detect to send back to the
websocket for display on minecraft servers and to discord.
"""

import json
from datetime import datetime
from src.debug import is_debug
from src.broadcast import broadcast_to_all
import src.regexes


EVENT_MESSAGES = {
    "join": "joined the server.",
    "part": "left the server.",
    "ban": "was banned from the server.",
    "pardon": "was unbanned from the server.",
}


def parse_output(output, server): # pylint: disable=too-many-branches, too-many-return-statements
    """
    Parse websocket output into something we can use.
    """
    if not isinstance(server, dict) or not isinstance(server.get("external_id"), str):
        message = f"[ERROR] Invalid server object passed to parse_output: {server!r}"
        if is_debug():
            print(message)
        return None

    server_name = server["external_id"].lower()

    if not server_name:
        message = "[ERROR] Server external_id missing. Did you assign one in Pelican?"
        if is_debug():
            print(message)
        return None

    if is_debug():
        print(f"[{server_name}] {output}")

    server_regexes = getattr(src.regexes, server_name, None)

    if not server_regexes:
        message = f"No regexes found for server: {server_name}"
        if is_debug():
            print(message)
        return None

    for event_type, regex in server_regexes.items():
        match = regex.match(output)

        if not match:
            continue

        groups = match.groupdict()

        if groups.get("server", "").lower() != server_name:
            continue

        user = groups.get("user")
        time = time_cvt(groups.get("time"))
        message = groups.get("message")

        if event_type == "message":
            return build_chat_message(
                server_name,
                server,
                time,
                user,
                message
            )

        if event_type == "advancement":
            return build_event(
                event_type,
                server_name,
                server,
                time,
                user,
                groups.get("advancement")
            )

        if event_type in EVENT_MESSAGES:
            return build_event(
                event_type,
                server_name,
                server,
                time,
                user,
                EVENT_MESSAGES[event_type]
            )

        print("[ERROR] Unexpected message in bagging area.")
        return None

    return None


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
    tellraw_components = [
        {"text": f"[{server}] ", "color": "red"},
        {"text": f"<{user}> ", "color": "blue"},
        {"text": message, "color": "white"},
    ]
    data = f"tellraw @a {json.dumps(tellraw_components)}\n"

    msg = f"[{server}] <**{user}**> {message}"
    broadcast_to_all(origin, data, msg, except_origin=True)

    if is_debug():
        print(f"[{server}] [{time}] <{user}> {message}")
    return msg


def build_discord_chat_message(message) -> str:
    """
    Build and broadcast a chat message that originated in Discord out to
    every connected Minecraft server.

    Args:
        message: Discord message data, as emitted by DiscordClient.on_message
            (a dict with 'message', 'sender' and 'source' keys).
    """
    if message["source"] != "discord":
        return None

    sender = message["sender"]
    text = message["message"]

    tellraw_components = [
        {"text": "[discord] ", "color": "aqua"},
        {"text": f"<{sender}> ", "color": "blue"},
        {"text": text, "color": "white"},
    ]
    data = f"tellraw @a {json.dumps(tellraw_components)}\n"

    msg = f"[discord] <**{sender}**> {text}"

    # broadcast_to_all only sends over the socket when except_origin is
    # True, so use the same pattern as build_chat_message. The synthetic
    # origin's external_id will never match a real Minecraft server name,
    # so the message reaches every connected server. relay_to_discord is
    # False because this message originated in Discord: relaying it back
    # would echo the sender's own message into the same channel.
    broadcast_to_all(
        {"external_id": "discord"}, data, msg,
        except_origin=True, relay_to_discord=False,
    )

    if is_debug():
        print(f"[discord] <{sender}> {text}")

    return msg


def build_event(event_type, server, origin, time, user, event=None) -> str: # pylint: disable=too-many-arguments, too-many-positional-arguments
    """
    Build and broadcast a server event.
    """
    match event_type:
        case "advancement":
            event_text = f"made the advancement: **{event}**"
            tellraw_components = [
                {"text": f"{user} made the advancement: ", "color": "blue"},
                {"text": event, "color": "yellow"},
            ]

        case "join" | "part" | "ban" | "pardon":
            event_text = EVENT_MESSAGES[event_type]
            tellraw_components = [
                {"text": f"{user} {event_text}", "color": "blue"},
            ]

        case _:
            event_text = event or ""
            tellraw_components = [
                {"text": f"{user} {event_text}", "color": "blue"},
            ]

    prefix_component = {"text": f"[mc:{server}] ", "color": "red"}
    data = f"tellraw @a {json.dumps([prefix_component] + tellraw_components)}\n"

    message = f"[{server}] {user} {event_text}\n"
    output = f"[{server}] [{time}] {user} {event_text}"

    broadcast_to_all(origin, data, message, except_origin=True)

    if is_debug():
        print(output)

    return output
