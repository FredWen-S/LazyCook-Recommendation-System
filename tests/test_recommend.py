from recommend import recommend

def test_basic_hit():
    r = recommend(["番茄","鸡蛋"])
    assert any(x["name"]=="番茄炒蛋" for x in r)

def test_alias():
    r = recommend(["西红柿","蛋"])
    assert any(x["name"]=="番茄炒蛋" for x in r)

def test_time_filter():
    r = recommend(["西兰花","蒜"], time_limit=10)
    assert all((x["time"] or 0) <= 10 for x in r)
