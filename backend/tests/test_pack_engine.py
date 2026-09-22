from app.services.pack_engine import StopItem, pack_route


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


def test_back_segment_not_packed_into_front_bag():
    # back stop fits the front bag by weight/volume but must get its own bag
    stops = [
        StopItem(1, 1, 2.0, 3.0, segment="front"),
        StopItem(2, 2, 1.0, 1.0, segment="back"),
    ]
    result = pack_route(stops, max_weight=8.0, max_volume=10.0)
    assert len(result.bags) == 2
    assert result.bags[0].segment == "front"
    assert [i.stop_id for i in result.bags[0].items] == [1]
    assert result.bags[1].segment == "back"
    assert [i.stop_id for i in result.bags[1].items] == [2]


def test_back_segment_waits_for_unprocessed_front_stops():
    # back stop at seq 2 is earlier than the front stop at seq 3, yet the
    # back bag opens only after every front stop is bagged or rejected
    stops = [
        StopItem(1, 1, 2.0, 3.0, segment="front"),
        StopItem(2, 2, 1.0, 1.0, segment="back"),
        StopItem(3, 3, 2.0, 3.0, segment="front"),
    ]
    result = pack_route(stops, max_weight=8.0, max_volume=10.0)
    assert len(result.bags) == 2
    assert [i.stop_id for i in result.bags[0].items] == [1, 3]
    assert result.bags[1].segment == "back"
    assert [i.stop_id for i in result.bags[1].items] == [2]


def test_back_segment_packs_after_all_front_rejected():
    # rejected front stops count as processed and do not block the back segment
    stops = [
        StopItem(1, 1, 9.0, 1.0, segment="front"),
        StopItem(2, 2, 1.0, 1.0, segment="back"),
        StopItem(3, 3, 1.0, 1.0, segment="back"),
    ]
    result = pack_route(stops, max_weight=5.0, max_volume=5.0)
    assert [r[0].stop_id for r in result.rejects] == [1]
    assert len(result.bags) == 1
    assert result.bags[0].segment == "back"
    assert [i.stop_id for i in result.bags[0].items] == [2, 3]
