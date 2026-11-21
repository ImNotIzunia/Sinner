import logging

from sinner import config
from sinner.bot import Sinner

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    config.validate()
    Sinner().run(config.TOKEN, log_handler=None)

if __name__ == "__main__":
    main()

