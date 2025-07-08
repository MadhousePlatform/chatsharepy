from datetime import datetime

from src.debug import DEBUG_MODE
import src.regexes


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
                match event_type:
                    case "message":
                        user = groups.get("user", "")
                        message = groups.get("message", "")
                        time = groups.get("time", "")

                        try:
                            # Parse the 24-hour time string
                            t = datetime.strptime(time, "%H:%M:%S")
                            # Format as 12-hour time
                            time = t.strftime("%I:%M%p")
                        except ValueError:
                            return time  # fallback if input is malformed

                        if user != "" and message != "":
                            build_chat_message(f"[{server_name}] [{time}] <{user}> {message}")
                    case _:
                        print("[ERROR] Unexpected message in bagging area.")
            else:
                # Server name in log line didn't match this server, ignore match
                continue
    return None


def build_chat_message(data):
    print(f"parsed: {data}")


def build_event(type, server, user):
    return False
