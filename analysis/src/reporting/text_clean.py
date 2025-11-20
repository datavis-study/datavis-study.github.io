import math
import numbers
import re
from typing import Optional


_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.;:!?])")
_MULTISPACE_RE = re.compile(r"[ \t]{2,}")


def _collapse_blank_lines(lines: list[str]) -> list[str]:
	new_lines: list[str] = []
	blank = False
	for ln in lines:
		if ln == "":
			if not blank:
				new_lines.append("")
			blank = True
		else:
			new_lines.append(ln)
			blank = False
	return new_lines


def clean_text(text: Optional[str]) -> str:
	"""
	Minimal text cleanup:
	- treat None/NaN as empty
	- normalize newlines
	- trim each line and collapse multiple spaces
	- remove spaces before punctuation
	- collapse runs of blank lines to a single blank line
	"""
	if text is None:
		return ""

	# Pandas often represents missing values as NaN (numpy.float64).
	# Avoid printing the literal string "nan" in the report.
	try:
		if isinstance(text, numbers.Real) and math.isnan(float(text)):
			return ""
	except Exception:
		# If the check fails, just fall back to normal string handling below.
		pass

	t = str(text).replace("\r\n", "\n").replace("\r", "\n")
	lines = [ln.strip() for ln in t.split("\n")]
	lines = [ _SPACE_BEFORE_PUNCT_RE.sub(r"\1", _MULTISPACE_RE.sub(" ", ln)) for ln in lines ]
	lines = _collapse_blank_lines(lines)
	out = "\n".join(lines).strip()
	return out


