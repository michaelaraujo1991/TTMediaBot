from enum import Flag
import logging
from logging.handlers import RotatingFileHandler
import os
import sys

from bot import vars

class Mode(Flag):
    STDOUT = 1
    FILE = 2
    STDOUT_AND_FILE = STDOUT|FILE

def initialize_logger(config, file):
    logging.addLevelName(5, "PLAYER_DEBUG")
    level = logging.getLevelName(config['level'])
    formatter = logging.Formatter(config['format'])
    handlers = []
    try:
        mode = Mode(config["mode"]) if isinstance(config["mode"], int) else Mode.__members__[config["mode"]]
    except KeyError:
        sys.exit("Invalid log mode name")
    if mode & Mode.FILE == Mode.FILE:
        if not file:
            file = config["file_name"]
        rotating_file_handler = RotatingFileHandler(filename=file, mode='a', maxBytes=config['max_file_size'] * 1024, backupCount=config['backup_count'], encoding='UTF-8')
        rotating_file_handler.setFormatter(formatter)
        rotating_file_handler.setLevel(level)
        handlers.append(rotating_file_handler)
    if mode & Mode.STDOUT == Mode.STDOUT:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(level)
        handlers.append(stream_handler)
    logging.basicConfig(level=level, format=config['format'], handlers=handlers)
