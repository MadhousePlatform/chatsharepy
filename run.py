#!/usr/bin/python3
import threading

from src.chatshare import main

threading.Thread(target=main, daemon=True).start()