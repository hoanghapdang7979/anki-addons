"""Compact per-habit tick storage: one bit per calendar day (ordinal), base64 in JSON.

Ticks form a grow-only set, so two copies (e.g. config vs local shadow) merge
with a plain union. No aqt/anki imports.
"""

import base64
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, eq=False)
class Bitmap:
    """Bit i of `data` (LSB first within each byte) means day `epoch + i` is ticked."""

    epoch: int = 0
    data: bytes = b""

    def is_set(self, ordinal: int) -> bool:
        i = ordinal - self.epoch
        if i < 0 or i >= len(self.data) * 8:
            return False
        return bool((self.data[i >> 3] >> (i & 7)) & 1)

    def ticked_ordinals(self) -> set[int]:
        return {
            self.epoch + i
            for i in range(len(self.data) * 8)
            if (self.data[i >> 3] >> (i & 7)) & 1
        }

    def with_bit(self, ordinal: int, value: bool) -> "Bitmap":
        ticks = self.ticked_ordinals()
        if value:
            ticks.add(ordinal)
        else:
            ticks.discard(ordinal)
        return _from_ordinals(ticks)

    def to_dict(self) -> dict:
        return {"epoch": self.epoch, "bits": base64.b64encode(self.data).decode("ascii")}

    @classmethod
    def from_dict(cls, raw: dict | None) -> "Bitmap":
        """Parse a stored value. Raises ValueError on malformed data so callers
        never silently overwrite a corrupt-but-recoverable value with an empty one."""
        if not raw:
            return cls()
        epoch = raw.get("epoch")
        bits = raw.get("bits")
        if isinstance(epoch, bool) or not isinstance(epoch, int):
            raise ValueError(f"bad epoch: {epoch!r}")
        if not isinstance(bits, str):
            raise ValueError(f"bad bits: {bits!r}")
        return cls(epoch=epoch, data=base64.b64decode(bits.encode("ascii"), validate=True))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Bitmap):
            return NotImplemented
        return self.ticked_ordinals() == other.ticked_ordinals()


def _from_ordinals(ordinals: set[int]) -> Bitmap:
    if not ordinals:
        return Bitmap()
    epoch = min(ordinals)
    data = bytearray(((max(ordinals) - epoch) >> 3) + 1)
    for o in ordinals:
        i = o - epoch
        data[i >> 3] |= 1 << (i & 7)
    return Bitmap(epoch=epoch, data=bytes(data))


def union(a: Bitmap, b: Bitmap) -> Bitmap:
    return _from_ordinals(a.ticked_ordinals() | b.ticked_ordinals())


def toggle_today(bitmap: Bitmap, today: date) -> Bitmap:
    """Flip only today's bit. Deliberately takes no other date, so past days
    cannot be changed through this path."""
    ordinal = today.toordinal()
    return bitmap.with_bit(ordinal, not bitmap.is_set(ordinal))
