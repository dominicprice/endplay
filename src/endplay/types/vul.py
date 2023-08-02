__all__ = ["Vul"]

from enum import IntEnum


class Vul(IntEnum):
    "Encodes the vulnerability"
    none = 0
    both = 1
    ns = 2
    ew = 3

    @staticmethod
    def find(name: str) -> "Vul":
        "Convert a string into a Vul object"
        if name.lower() in ["n", "s", "ns"]:
            return Vul.ns
        elif name.lower() in ["e", "w", "ew"]:
            return Vul.ew
        elif name.lower() in ["all", "both", "a", "b"]:
            return Vul.both
        elif name.lower() in ["", "none", "-", "luv"]:
            return Vul.none
        else:
            raise ValueError(f"could not convert '{name}' to Vul")

    @staticmethod
    def from_lin(s: str) -> "Vul":
        """
        Convert a BBO LIN string of vulnerability into a Vul object.
        The conversion is determined by o=none, e=ew, n=ns, b=both
        """
        try:
            if s == "":
                raise ValueError
            return Vul("obne".index(s.lower()))
        except ValueError:
            raise ValueError(
                f"invalid lin vulnerability '{s}': must be one of o, b, n, e"
            )

    def to_lin(self) -> str:
        return "obne"[self]

    @staticmethod
    def from_board(board_no: int) -> "Vul":
        ":return: The vulnerability of the specified board"
        i = board_no - 1
        shift = (i // 4) % 4
        return [Vul.none, Vul.ns, Vul.ew, Vul.both][(i + shift) % 4]

    @property
    def abbr(self) -> str:
        "A short string representation of the vulnerability"
        if self == Vul.none:
            return "-"
        if self == Vul.both:
            return "A"
        return self.name.upper()
