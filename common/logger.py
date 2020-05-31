#!/usr/bin/env python3
import os
import logging


def setup_logger(id):
    loglevel = os.environ.get("LOGLEVEL", "WARNING")
    FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=loglevel)
    logger = logging.getLogger(id)
    return logger


def main():
    logger = setup_logger(__file__)
    logger.error("This is an error")
    logger.warning("This is warning")
    logger.info("This is info")
    logger.debug("This is a debug message")


if __name__ == "__main__":
    main()