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
	- normalize newlines
	- trim each line and collapse multiple spaces
	- remove spaces before punctuation
	- collapse runs of blank lines to a single blank line
	"""
	if text is None:
		return ""
	t = str(text).replace("\r\n", "\n").replace("\r", "\n")
	lines = [ln.strip() for ln in t.split("\n")]
	lines = [ _SPACE_BEFORE_PUNCT_RE.sub(r"\1", _MULTISPACE_RE.sub(" ", ln)) for ln in lines ]
	lines = _collapse_blank_lines(lines)
	out = "\n".join(lines).strip()
	return out


