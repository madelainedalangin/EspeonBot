import pytest
from helpers import *

################
# VALID INPUTS #
################

def test_days():
    assert parse_duration("7d") == 10080

def test_days_uppercase():
    assert parse_duration("7D") == 10080

def test_weeks():
    assert parse_duration("2w") == 20160

def test_months():
    assert parse_duration("6mo") == 259200

def test_one_day():
    assert parse_duration("1d") == 1440

def test_one_month():
    assert parse_duration("1mo") == 43200

def test_large_number():
    assert parse_duration("365d") == 525600

def test_zero_days():
    assert parse_duration("0d") == 0
    
def test_hours():
    assert parse_duration("3h") == 180

def test_minutes():
    assert parse_duration("30mi") == 30

##################
# INVALID INPUTS #
##################
def test_invalid_unit():
    with pytest.raises(ValueError, match="Unknown unit"):
        parse_duration("67x")

def test_invalid_unit_y():
    with pytest.raises(ValueError, match="Unknown unit"):
        parse_duration("3y")

def test_no_number():
    with pytest.raises(ValueError):
        parse_duration("d")

def test_empty_string():
    with pytest.raises(Exception):
        parse_duration("")

def test_just_number():
    with pytest.raises(Exception):
        parse_duration("7")

def test_negative():
    with pytest.raises(ValueError, match="positive"):
        parse_duration("-1d")

def test_float_number():
    with pytest.raises(ValueError):
        parse_duration("1.5d")

def test_none():
    with pytest.raises(Exception):
        parse_duration(None)

def test_invalid_mo_typo():
    with pytest.raises(ValueError):
        parse_duration("3mx")

def test_invalid_mi_typo():
    with pytest.raises(ValueError):
        parse_duration("3mu")