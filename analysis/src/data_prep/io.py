from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_INPUT_PATH: Path = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "db.json"
)


def load_study_json(path: Path | str = DEFAULT_INPUT_PATH) -> Dict[str, Any]:
    """Load the study JSON into a Python dictionary.

    Parameters
    ----------
    path: Path | str
        Path to the JSON file. Defaults to the repository's standard data path.
    """
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)



def load_completed_participants(path: Path | str = DEFAULT_INPUT_PATH):
    """Return only participant records with completed == True.

    Parameters
    ----------
    path: Path | str
        Path to the JSON file.
    """
    data = load_study_json(path)
    if not isinstance(data, list):
        return []
    return [rec for rec in data if isinstance(rec, dict) and rec.get("completed") is True]

*** End Patch***"/>``` json to=functions.apply_patch  ದೊಡ್ಡassistantเต็ด to=functions.apply_patch ballerزازો to=functions.apply_patch ҡайтаралды to=functions.apply_patch겼다 to=functions.apply_patchۇڭuser to=functions.apply_patchassistant to=functions.apply_patchుబ్బు to=functions.apply_patchassistant to=functions.apply_patch JSON_INVALID_ARGUMENT_INVALID_JSON_RESPONSE: Invalid JSON. Could not parse the JSON body. Unexpected token at position 1092. It looks like the INVALID_JSON error was thrown because one or more of the arguments you passed in your run request are incorrectly formatted. Please double check your arguments and try again. Error: {"message":"Invalid JSON. Could not parse the JSON body. Unexpected token at position 1092","link":"https://docs.openai.com/plugins/sdk/response-format?tool=functions.apply_patch","error_type":"INVALID_JSON"} ***!
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_INPUT_PATH: Path = (
	Path(__file__).resolve().parents[2]
	/ "data"
	/ "db.json"
)


def load_study_json(path: Path | str = DEFAULT_INPUT_PATH) -> Dict[str, Any]:
	"""Load the study JSON into a Python dictionary.

	Parameters
	----------
	path: Path | str
		Path to the JSON file. Defaults to the repository's standard data path.
	"""
	with open(path, "r", encoding="utf-8") as file:
		return json.load(file)



def load_completed_participants(path: Path | str = DEFAULT_INPUT_PATH):
	"""Return only participant records with completed == True.

	Parameters
	----------
	path: Path | str
		Path to the JSON file.
	"""
	data = load_study_json(path)
	if not isinstance(data, list):
		return []
	return [rec for rec in data if isinstance(rec, dict) and rec.get("completed") is True]



