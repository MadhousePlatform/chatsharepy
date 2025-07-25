"""
debug.py
Checks for --debug and assigned DEBUG_MODE a value of True
"""

import argparse

# I don't like global variables but this will be useful
DEBUG_MODE = False


def parse_args():
    """
    Parse arguments to check for --debug.
    """
    global DEBUG_MODE  # pylint: disable=global-statement
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    DEBUG_MODE = args.debug
    return args

if __name__ == "__main__":
    parse_args()
