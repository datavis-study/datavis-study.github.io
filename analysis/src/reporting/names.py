import hashlib
from typing import Set

# Short, readable lists (expand as needed)
ADJECTIVES = [
	"brave", "calm", "clever", "bright", "eager", "gentle", "happy", "kind", "lively", "noble",
	"proud", "quick", "quiet", "sharp", "smart", "swift", "wise", "witty", "bold", "cool",
	"merry", "neat", "jolly", "keen", "spry", "sunny", "tidy", "vivid", "zesty", "chill",
]

ANIMALS = [
	"ant", "bear", "bee", "bird", "cat", "cow", "crab", "deer", "dog", "duck",
	"eagle", "fox", "frog", "goat", "hare", "hawk", "lion", "lynx", "mole", "moose",
	"mouse", "otter", "owl", "panda", "seal", "shark", "sheep", "snake", "tiger", "whale",
]


def _hash_bytes(pid: str) -> bytes:
	h = hashlib.sha256(pid.encode("utf-8")).digest()
	return h


def _pick_from_hash(hb: bytes, offset: int, modulo: int) -> int:
	# Take 4 bytes starting at offset, wrap if needed
	chunk = hb[offset:offset + 4]
	if len(chunk) < 4:
		chunk = (chunk + hb[:4 - len(chunk)])
	val = int.from_bytes(chunk, byteorder="big", signed=False)
	return val % modulo


def generate_human_name(participant_id: str, used: Set[str] | None = None) -> str:
	"""
	Deterministically generate a readable 'adjective-animal-##' name from a participant id.
	We include a 2-digit suffix to reduce collisions; if a collision still occurs in 'used',
	increment the number deterministically until unique.
	"""
	hb = _hash_bytes(participant_id or "")
	adj = ADJECTIVES[_pick_from_hash(hb, 0, len(ADJECTIVES))]
	ani = ANIMALS[_pick_from_hash(hb, 4, len(ANIMALS))]
	num = _pick_from_hash(hb, 8, 100)
	name = f"{adj}-{ani}-{num:02d}"
	if used is None:
		return name
	# Resolve collisions by stepping number in a deterministic stride
	if name not in used:
		return name
	for step in range(1, 101):
		alt = f"{adj}-{ani}-{(num + step) % 100:02d}"
		if alt not in used:
			return alt
	# As a last resort (extremely unlikely), append a single extra digit
	return f"{adj}-{ani}-{num:02d}0"


