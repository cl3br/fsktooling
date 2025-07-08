import logging
from pathlib import Path

import __main__


def get_logger(module_name: str, file_path: str) -> logging.Logger:
    if module_name == "__main__":
        return logging.getLogger(Path(file_path).stem)
    elif Path(__main__.__file__).stem == "DEUMeldeformularKonverter":
        return logging.getLogger("DEUMeldeformularKonverter." + module_name)
    else:
        return logging.getLogger(module_name)
