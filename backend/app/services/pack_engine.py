"""Route-order bag packing with weight + volume caps; reject when exceed.

订户点分段：前段 (front) 与后段 (rear)。
- 装袋仍严格按 seq 顺序，但先把全部前段站点处理完（入袋或拒收），
  再开后段袋；后段首站一定另开新袋，因此后段站点不会进入任何
  仍含前段站点的袋。
- 前段站点被拒收视为该站已处理，不堵住后段；前段全部拒收后，
  后段站点照常可以装袋。
- 后段站点在 seq 上可能早于部分前段站出现，此时它必须等到前段
  全部处理完才入袋。
"""

from __future__ import annotations

from dataclasses import dataclass, field

SEG_FRONT = "front"
SEG_REAR = "rear"


@dataclass(frozen=True)
class StopItem:
    stop_id: int
    seq: int
    weight_kg: float
    volume_l: float
    label: str = ""
    segment: str = SEG_FRONT


@dataclass
class Bag:
    bag_index: int
    items: list[StopItem] = field(default_factory=list)
    weight_kg: float = 0.0
    volume_l: float = 0.0
    segment: str = SEG_FRONT


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
    stops: list[StopItem],
    segment: str,
    max_weight: float,
    max_volume: float,
    bags: list[Bag],
    rejects: list[tuple[StopItem, str]],
    current: Bag | None,
) -> Bag | None:
    """Pack one segment's stops (already ordered by seq).

    Entering the rear segment forces a fresh bag so a rear stop can never
    join a bag that still holds front stops.
    """
    if segment == SEG_REAR:
        current = None

    for item in stops:
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

    return current


def pack_route(
    stops: list[StopItem],
    max_weight: float,
    max_volume: float,
) -> PackResult:
    ordered = sorted(stops, key=lambda s: s.seq)
    front = [s for s in ordered if s.segment != SEG_REAR]
    rear = [s for s in ordered if s.segment == SEG_REAR]

    bags: list[Bag] = []
    rejects: list[tuple[StopItem, str]] = []

    current = _pack_segment(front, SEG_FRONT, max_weight, max_volume, bags, rejects, None)
    _pack_segment(rear, SEG_REAR, max_weight, max_volume, bags, rejects, current)

    # 拒收按 seq 顺序展示；袋顺序固定为前段在前、后段在后
    rejects.sort(key=lambda r: r[0].seq)

    return PackResult(bags=bags, rejects=rejects)
