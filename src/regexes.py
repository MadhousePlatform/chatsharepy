"""Regexes for parsing log lines."""
import re

vanilla = {
    "message": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO]:"
        r" <(?P<user>[^>]+)> (?P<message>.+)"),
    "join": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO]: "
        r"(?P<user>\S+) joined the game"),
    "part": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO]: "
        r"(?P<user>\S+) left the game"),
    "ban": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO]: "
        r"(?P<action>Banned) (?P<user>\S+)(?:: (?P<message>.+))?"),
    "pardon": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO]: "
        r"(?P<action>Unbanned) (?P<user>\S+)(?:: (?P<message>.+))?"),
    "advancement": re.compile(
        r"\[(?P<server>[^\]]+)] \[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO]: "
        r"(?P<user>\w+) has made the advancement \[(?P<advancement>[^\]]+)]"),
}

atm10 = {
    "message": re.compile(
        r"(?:\x1b\[[0-9;]*m)*\[(?P<server>[^\]]+)] (?:\x1b\[[0-9;]*m)*"
        r"\[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO] \[minecraft/MinecraftServer]:"
        r" <(?P<user>.+?)>> (?P<message>.+)"
    ),
    "join": re.compile(
        r"(?:\x1b\[[0-9;]*m)*\[(?P<server>[^\]]+)] (?:\x1b\[[0-9;]*m)*"
        r"\[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO] \[minecraft/MinecraftServer]:"
        r" <(?P<user>.+?)>> joined the game"),
    "part": re.compile(
        r"(?:\x1b\[[0-9;]*m)*\[(?P<server>[^\]]+)] (?:\x1b\[[0-9;]*m)*"
        r"\[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO] \[minecraft/MinecraftServer]:"
        r" <(?P<user>.+?)>> left the game"),
    "ban": re.compile(
        r"(?:\x1b\[[0-9;]*m)*\[(?P<server>[^\]]+)] (?:\x1b\[[0-9;]*m)*"
        r"\[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO] \[minecraft/MinecraftServer]:"
        r" (?P<action>Banned) <(?P<user>.+?)>>(?:: (?P<message>.+))?"),
    "pardon": re.compile(
        r"(?:\x1b\[[0-9;]*m)*\[(?P<server>[^\]]+)] (?:\x1b\[[0-9;]*m)*"
        r"\[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO] \[minecraft/MinecraftServer]:"
        r" (?P<action>Unbanned) <(?P<user>.+?)>>(?:: (?P<message>.+))?"),
    "advancement": re.compile(
        r"(?:\x1b\[[0-9;]*m)*\[(?P<server>[^\]]+)] (?:\x1b\[[0-9;]*m)*"
        r"\[(?P<time>\d{2}:\d{2}:\d{2})] \[Server thread/INFO] \[minecraft/MinecraftServer]:"
        r" <(?P<user>.+?)>> has made the advancement \[(?P<advancement>[^\]]+)]"),
}

archex = atm10
tts = atm10