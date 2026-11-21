import json
import logging
import os
from pathlib import Path


log = logging.getLogger("sinner.state")


STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "state.json"


def load() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        log.warning("Reading of %s is impossible : %s", STATE_FILE, e)
        return {}


def save(data: dict) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, STATE_FILE)
    except OSError as e:
        log.warning("Writing of %s is impossible : %s", STATE_FILE, e)


