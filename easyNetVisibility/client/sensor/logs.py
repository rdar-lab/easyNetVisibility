import logging


def setup():
    FORMAT = '%(asctime)-15s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)
