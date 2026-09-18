"""
debug.py
Checks for --debug and provides debug mode state checking
"""

import argparse

debug_state = {'enabled': False}


def is_debug() -> bool:
    """Returns whether debug mode is enabled."""
    return debug_state['enabled']


def parse_args():
    """Parse arguments to check for --debug."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    debug_state['enabled'] = args.debug
    return args


if __name__ == "__main__":
    parse_args()
