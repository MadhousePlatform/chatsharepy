import argparse

# I don't like global variables but this will be useful
DEBUG_MODE = False


def parse_args():
    global DEBUG_MODE
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    DEBUG_MODE = args.debug


parse_args()