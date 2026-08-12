from decimal import Decimal

from geologparser.normalization import feet_to_metres, metres_to_feet


def test_exact_foot_metre_conversion():
    assert feet_to_metres("100") == Decimal("30.4800")
    assert metres_to_feet("30.48") == Decimal("1.0E+2")

