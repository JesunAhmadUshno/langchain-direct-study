import math

from study.analyze import _passk, t_ppf


def test_t_ppf_known_values():
    assert abs(t_ppf(0.95, 11) - 1.7959) < 0.01
    assert abs(t_ppf(0.975, 5) - 2.5706) < 0.01
    assert abs(t_ppf(0.95, 30) - 1.6973) < 0.01


def test_passk_unbiased_estimator():
    assert _passk(8, 8, 8) == 1.0
    assert _passk(0, 8, 1) == 0.0
    assert _passk(7, 8, 1) == 0.875
    assert math.isclose(_passk(4, 8, 2), 6 / 28)
    assert _passk(3, 8, 4) == 0.0
