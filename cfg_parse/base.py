import uuid
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, Generic, Iterable, Iterator, Optional, TypeVar

T = TypeVar("T")


class OrderedSet(Generic[T]):
    def __init__(self, iterable: Iterable[T] = None):  # type: ignore
        self._dict: dict[T, None] = dict.fromkeys(iterable if iterable else [])

    def add(self, item: T) -> None:
        self._dict[item] = None

    def discard(self, item: T) -> None:
        if item in self._dict:
            self._dict.pop(item)

    def extend(self, other) -> "OrderedSet":
        for symbol in other:
            self.add(symbol)
        return self

    def __bool__(self) -> bool:
        return bool(self._dict)

    def __contains__(self, item: T) -> bool:
        return item in self._dict

    def __iter__(self) -> Iterator[T]:
        return iter(self._dict.keys())

    def __len__(self) -> int:
        return len(self._dict)

    def __repr__(self) -> str:
        return f"OrderedSet({list(self._dict.keys())})"

    def __eq__(self, other) -> bool:
        if isinstance(other, OrderedSet):
            return list(self) == list(other)  # type: ignore
        return NotImplemented

    def __or__(self, other: "OrderedSet[T]") -> "OrderedSet[T]":
        return OrderedSet(self._dict.keys() | other._dict.keys())

    def __and__(self, other: "OrderedSet[T]") -> "OrderedSet[T]":
        return OrderedSet(self._dict.keys() & other._dict.keys())

    def copy(self):
        return deepcopy(self)


@dataclass
class Symbol:
    content: str
    s_type: "SymbolType"
    s_id: uuid.UUID = field(default_factory=lambda: uuid.uuid4())

    def __hash__(self):
        return hash((self.content, self.s_type, self.s_id))

    def __eq__(self, other):
        # Ensure equality is checked for all fields
        if not isinstance(other, Symbol):
            return False

        return (
            (self.content == other.content)
            and (self.s_type == other.s_type)
            and (self.s_id == other.s_id)
        )


class SymbolType(Enum):
    TERMINAL = 1
    NON_TERMINAL = 2
    REGEX = 3
    SPECIAL = 4


@dataclass
class SymbolGraph:
    tree: dict[Symbol, OrderedSet[Symbol]] = field(
        default_factory=lambda: defaultdict(OrderedSet)
    )
    initials: OrderedSet[Symbol] = field(default_factory=OrderedSet)
    finals: OrderedSet[Symbol] = field(default_factory=OrderedSet)

    def __eq__(self, other) -> bool:
        if isinstance(other, SymbolGraph):
            return (
                (self.initials == other.initials)
                and (self.tree == other.tree)
                and (self.finals == other.finals)
            )
        return NotImplemented

    def __bool__(self) -> bool:
        return bool(self.initials) and bool(self.tree) and bool(self.finals)

    def copy(self):
        return deepcopy(self)


class SymbolGraphType(Enum):
    STANDARD = 1
    NONE_ANY = 2
    NONE_ONCE = 3


@dataclass
class SymbolGraphState:
    graph: SymbolGraph
    label: str
    state: Optional[Symbol] = None
