from gridpoisonrag.stats import holm_adjust, mcnemar_exact


def test_mcnemar_exact_no_discordance():
    r = mcnemar_exact([(False, False), (True, True)])
    assert r.b == 0 and r.c == 0
    assert r.p_value == 1.0


def test_mcnemar_direction():
    r = mcnemar_exact([(True, False)] * 6 + [(False, True)] * 1)
    assert r.b == 6
    assert r.c == 1
    assert 0.0 <= r.p_value <= 1.0


def test_holm_is_bounded():
    vals = holm_adjust([0.01, 0.03, 0.8])
    assert all(0 <= x <= 1 for x in vals)
    assert vals[0] <= vals[1] <= vals[2]
