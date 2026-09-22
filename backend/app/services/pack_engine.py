"""Route-order bag packing with weight + volume caps; reject when exceed.

Segments: each stop belongs to the route's front (前段) or back (后段)
segment. Packing still follows seq within a segment, but the whole front
segment is settled first: no back bag opens while any front stop is
unprocessed (neither bagged nor rejected), and back stops never enter a
bag that holds front stops. A rejected front stop counts as processed and
does not block the back segment.
"""

from __future__ import annotations

from dataclasses import dataclass, field

FRONT = "front"
BACK = "back"


@dataclass(frozen=True)
class StopItem:
    stop_id: int
    seq: int
    weight_kg: float
    volume_l: float
    label: str = ""
    segment: str = FRONT


@dataclass
class Bag:
    bag_index: int
    segment: str = FRONT
    items: list[StopItem] = field(default_factory=list)
    weight_kg: float = 0.0
    volume_l: float = 0.0


@dataclass(frozen=True)
class PackResult:
    bags: list[Bag]
    rejects: list[tuple[StopItem, str]]


def can_fit(bag: Bag, item: StopItem, max_weight: float, max_volume: float) -> bool:
    return (
        bag.weight_kg + item.weight_kg <= max_weight + 1e-9
        and bag.volume_l + item.volume_l <= max_volume + 1e-9
    )


def _pack_segment(
    ordered: list[StopItem],
    segment: str,
    bags: list[Bag],
    rejects: list[tuple[StopItem, str]],
    max_weight: float,
    max_volume: float,
) -> None:
    current: Bag | None = None
    for item in ordered:
        if item.weight_kg > max_weight or item.volume_l > max_volume:
            reason = []
            if item.weight_kg > max_weight:
                reason.append(f"超重 {item.weight_kg}>{max_weight}")
            if item.volume_l > max_volume:
                reason.append(f"超体积 {item.volume_l}>{max_volume}")
            rejects.append((item, "；".join(reason)))
            continue

        if current is None or not can_fit(current, item, max_weight, max_volume):
            current = Bag(bag_index=len(bags) + 1, segment=segment)
            bags.append(current)

        if not can_fit(current, item, max_weight, max_volume):
            # should not happen after single-item check, but keep safe
            rejects.append((item, "无法装入新袋"))
            continue

        current.items.append(item)
        current.weight_kg += item.weight_kg
        current.volume_l += item.volume_l


def pack_route(
    stops: list[StopItem],
    max_weight: float,
    max_volume: float,
) -> PackResult:
    ordered = sorted(stops, key=lambda s: s.seq)
    bags: list[Bag] = []
    rejects: list[tuple[StopItem, str]] = []

    # Front segment is fully settled (bagged or rejected) before the first
    # back bag opens, so back stops never share a bag with front stops and a
    # rejected front stop never blocks the back segment.
    _pack_segment(
        [s for s in ordered if s.segment != BACK],
        FRONT,
        bags,
        rejects,
        max_weight,
        max_volume,
    )
    _pack_segment(
        [s for s in ordered if s.segment == BACK],
        BACK,
        bags,
        rejects,
        max_weight,
        max_volume,
    )

    return PackResult(bags=bags, rejects=rejects)
