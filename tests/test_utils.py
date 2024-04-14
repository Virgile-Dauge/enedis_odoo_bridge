import pytest

from datetime import date
from enedis_odoo_bridge.utils import gen_dates, pro_rata

__author__ = "Virgile"
__copyright__ = "Virgile"
__license__ = "GPL-3.0-only"


def test_gen_dates():
    """API Tests"""
    ...

def test_pro_rata_same_month():
    start_date = date(2022, 1, 15)
    end_date = date(2022, 1, 30)
    assert pro_rata(start_date, end_date) == 16/31

def test_pro_rata_next_month():
    start_date = date(2022, 1, 15)
    end_date = date(2022, 2, 15)
    assert pro_rata(start_date, end_date) == 17/31 + 15/28

def test_pro_rata_different_years():
    start_date = date(2022, 12, 15)
    end_date = date(2023, 1, 15)
    assert pro_rata(start_date, end_date) == 17/31 + 15/31

def test_pro_rata_invalid_dates():
    with pytest.raises(ValueError):
        pro_rata(date(2022, 1, 15), date(2021, 1, 15))


