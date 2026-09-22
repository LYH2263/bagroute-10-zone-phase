from app.services.pack_engine import SEG_FRONT, SEG_REAR, StopItem, pack_route


def test_packs_in_route_order_splitting_bags():
    stops = [
        StopItem(1, 1, 2.0, 3.0),
        StopItem(2, 2, 2.5, 3.0),
        StopItem(3, 3, 1.0, 1.0),
    ]
    result = pack_route(stops, max_weight=4.0, max_volume=10.0)
    assert len(result.bags) == 2
    assert [i.stop_id for i in result.bags[0].items] == [1]
    assert [i.stop_id for i in result.bags[1].items] == [2, 3]
    assert not result.rejects


def test_reject_oversized_stop():
    stops = [StopItem(1, 1, 9.0, 1.0, "大件"), StopItem(2, 2, 1.0, 1.0)]
    result = pack_route(stops, max_weight=5.0, max_volume=5.0)
    assert len(result.rejects) == 1
    assert result.rejects[0][0].stop_id == 1
    assert len(result.bags) == 1
    assert result.bags[0].items[0].stop_id == 2


def test_volume_cap_triggers_new_bag():
    stops = [StopItem(1, 1, 1.0, 4.0), StopItem(2, 2, 1.0, 4.0)]
    result = pack_route(stops, max_weight=10.0, max_volume=5.0)
    assert len(result.bags) == 2


def _segments(result):
    return [[it.segment for it in b.items] for b in result.bags]


def _bag_of(result, stop_id):
    for idx, bag in enumerate(result.bags):
        if any(it.stop_id == stop_id for it in bag.items):
            return idx
    return None


def test_rear_stop_never_enters_front_bag_even_if_seq_earlier():
    # 后段站 seq=2 早于前段站 seq=3；前段 1、3 合装一袋，
    # 后段 2 即使在顺序上夹在中间，也必须等前段处理完、另开后段袋。
    stops = [
        StopItem(1, 1, 2.0, 3.0, segment=SEG_FRONT),
        StopItem(2, 2, 1.0, 2.0, segment=SEG_REAR),
        StopItem(3, 3, 1.5, 2.0, segment=SEG_FRONT),
    ]
    result = pack_route(stops, max_weight=4.0, max_volume=10.0)

    assert len(result.bags) == 2
    front_bag, rear_bag = result.bags
    # 前段袋含全部前段站、不含任何后段站
    assert [i.stop_id for i in front_bag.items] == [1, 3]
    assert front_bag.segment == SEG_FRONT
    assert all(i.segment == SEG_FRONT for i in front_bag.items)
    # 后段袋独立
    assert [i.stop_id for i in rear_bag.items] == [2]
    assert rear_bag.segment == SEG_REAR
    # 袋号：前段袋在前，后段袋在后
    assert front_bag.bag_index == 1
    assert rear_bag.bag_index == 2
    assert not result.rejects


def test_front_reject_does_not_block_rear():
    # 前段全部因超重拒收；后段站仍应正常装袋，不被堵住。
    stops = [
        StopItem(1, 1, 9.0, 1.0, segment=SEG_FRONT),
        StopItem(2, 2, 2.0, 1.0, segment=SEG_REAR),
        StopItem(3, 3, 2.0, 2.0, segment=SEG_REAR),
    ]
    result = pack_route(stops, max_weight=5.0, max_volume=5.0)

    assert {s.stop_id for s, _ in result.rejects} == {1}
    assert len(result.bags) == 1
    bag = result.bags[0]
    assert bag.segment == SEG_REAR
    assert [i.stop_id for i in bag.items] == [2, 3]


def test_rear_waits_until_all_front_processed():
    # 后段站 seq 最早，且前段有站在容量上会拆成多袋；
    # 后段仍必须落在所有前段袋之后、自成后段袋。
    stops = [
        StopItem(10, 1, 1.0, 1.0, segment=SEG_REAR),
        StopItem(1, 2, 3.0, 3.0, segment=SEG_FRONT),
        StopItem(2, 3, 3.0, 3.0, segment=SEG_FRONT),
        StopItem(3, 4, 3.0, 3.0, segment=SEG_FRONT),
    ]
    result = pack_route(stops, max_weight=4.0, max_volume=4.0)

    # 前段拆 3 袋，后段 1 袋
    assert len(result.bags) == 4
    assert all(b.segment == SEG_FRONT for b in result.bags[:3])
    rear_bag = result.bags[3]
    assert rear_bag.segment == SEG_REAR
    assert [i.stop_id for i in rear_bag.items] == [10]
    assert _bag_of(result, 10) == 3
    assert all(_segments(result)[i] == [SEG_FRONT] for i in range(3))
