import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def notify(message: str, is_error: bool = False):
    if is_error:
        logging.error(f"ALERT: {message}")
    else:
        logging.info(f"STATUS: {message}")
