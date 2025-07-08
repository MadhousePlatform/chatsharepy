import re

vanilla = {
    "message": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO]: <(?P<user>[^>]+)> (?P<message>.+)"),
    "join": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO]: (?P<user>\S+) joined the game"),
    "part": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO]: (?P<user>\S+) left the game"),
    "ban": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO]: (?P<action>Banned) (?P<user>\S+)(?:: (?P<message>.+))?"),
    "pardon": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO]: (?P<action>Unbanned) (?P<user>\S+)(?:: (?P<message>.+))?")
}

atm10 = {
    "message": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO] \[[^/]+/[^]]+]: <(?P<user>[^>]+)> (?P<message>.+)"),
    "join": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO] \[[^/]+/[^]]+]: (?P<user>\S+) joined the game"),
    "part": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO] \[[^/]+/[^]]+]: (?P<user>\S+) left the game"),
    "ban": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO] \[[^/]+/[^]]+]: Banned (?P<user>\S+): (?P<message>.+)"),
    "pardon": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO] \[[^/]+/[^]]+]: Unbanned (?P<user>\S+)")
}
