from __future__ import annotations

__all__ = ["Bid", "ContractBid", "PenaltyBid"]

from typing import Callable, Optional, TypeVar

from endplay.types.denom import Denom
from endplay.types.penalty import Penalty

T = TypeVar("T")


class Bid:
    """
    Base class representing an auction call. This class provides a convenience
    constructor from a string, but upon construction will automatically donwcast
    its type to one of :class:`ContractBid` or :class:`PenaltyBid` depending on the type of the
    call.

    :ivar alertable: Flag indicating whether the bid is alertable
    :vartype alertable: bool
    :ivar announcement: String transcription of the announcement for this bid
    :vartype announcement: Optional[str]
    """

    alertable: bool
    announcement: Optional[str]

    def __init__(
        self, name: str, alertable: bool = False, announcement: Optional[str] = None
    ):
        try:
            penalty = Penalty.find(name)
            object.__setattr__(self, "__class__", PenaltyBid)
            PenaltyBid.__init__(self, penalty, alertable, announcement)  # type: ignore
        except ValueError:
            level, denom = int(name[0]), Denom.find(name[1])
            object.__setattr__(self, "__class__", ContractBid)
            ContractBid.__init__(self, level, denom, alertable, announcement)  # type: ignore

    def as_contract(self) -> Optional[ContractBid]:
        """
        Returns a typecasts to `ContractBid` if this is a contract bid,
        otherwise returns None
        """
        return self if isinstance(self, ContractBid) else None

    def as_penalty(self) -> Optional[PenaltyBid]:
        """
        Returns a typecasts to `PenaltyBid` if this is a penalty bid, otherwise
        returns None
        """
        return self if isinstance(self, PenaltyBid) else None


class ContractBid(Bid):
    """
    Class representing a call that names a contract, i.e. has a level and strain

    :ivar level: The level of the call (between 1 and 7)
    :vartype level: int
    :ivar denom: The strain of the call
    :vartype strain: Denom
    :ivar alertable: Flag indicating whether the bid is alertable
    :vartype alertable: bool
    :ivar announcement: String transcription of the announcement for this bid
    :vartype announcement: Optional[str]
    """

    def __init__(
        self,
        level: int,
        denom: Denom,
        alertable: bool = False,
        announcement: Optional[str] = None,
    ):
        self.level = level
        self.denom = denom
        self.alertable = alertable
        self.announcement = announcement

    def __repr__(self):
        return f"ContractBid(denom={self.denom!r}, level={self.level!r}, alertable={self.alertable!r}, announcement={self.announcement!r})"

    def __str__(self):
        s = f"{self.level}{self.denom.abbr}"
        if self.alertable:
            s += "!"
        if self.announcement:
            s += "*"
        return s

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ContractBid):
            return False
        return (
            self.level == other.level
            and self.denom == other.denom
            and self.alertable == other.alertable
            and self.announcement == other.announcement
        )


class PenaltyBid(Bid):
    """
    Class representing a call that does not name a contract, i.e. pass, double or redouble

    :ivar penalty: The type of the call
    :vartype penalty: Penalty
    :ivar alertable: Flag indicating whether the bid is alertable
    :vartype alertable: bool
    :ivar announcement: String transcription of the announcement for this bid
    :vartype announcement: Optional[str]
    """

    def __init__(
        self,
        penalty: Penalty,
        alertable: bool = False,
        announcement: Optional[str] = None,
    ):
        self.penalty = penalty
        self.alertable = alertable
        self.announcement = announcement

    def __repr__(self):
        return f"PenaltyBid(penalty={self.penalty!r}, alertable={self.alertable!r}, announcement={self.announcement!r})"

    def __str__(self):
        s = self.penalty.abbr or "P"
        if self.alertable:
            s += "!"
        if self.announcement:
            s += "*"
        return s.upper()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PenaltyBid):
            return False
        return (
            self.penalty == other.penalty
            and self.alertable == other.alertable
            and self.announcement == other.announcement
        )
