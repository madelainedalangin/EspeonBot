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

def test_one_minute():
    assert parse_duration("1mi") == 1

def test_one_hour():
    assert parse_duration("1h") == 60

def test_one_week():
    assert parse_duration("1w") == 10080

# combined durations

def test_combined_hour_minutes():
    assert parse_duration("1h30mi") == 90

def test_combined_day_hours():
    assert parse_duration("1d12h") == 2160

def test_combined_week_days():
    assert parse_duration("2w3d") == 24480

def test_combined_uppercase():
    assert parse_duration("1H30MI") == 90

def test_combined_three_units():
    assert parse_duration("1d2h30mi") == 1590

def test_combined_week_day_hour():
    assert parse_duration("1w1d1h") == 11580

def test_combined_month_week():
    assert parse_duration("1mo1w") == 53280

def test_combined_all_units():
    assert parse_duration("1mo1w1d1h1mi") == 54781

def test_combined_mixed_case():
    assert parse_duration("2H45Mi") == 165

##################
# INVALID INPUTS #
##################

def test_invalid_unit():
    with pytest.raises(ValueError, match="not a valid duration"):
        parse_duration("67x")

def test_invalid_unit_y():
    with pytest.raises(ValueError, match="not a valid duration"):
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
    with pytest.raises(ValueError, match="not a valid duration"):
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

def test_spaces_between():
    with pytest.raises(ValueError):
        parse_duration("1h 30mi")

def test_letters_only():
    with pytest.raises(ValueError):
        parse_duration("abc")

def test_duplicate_units():
    # "1h2h" is valid syntax, just adds up
    assert parse_duration("1h2h") == 180

def test_zero_combined():
    assert parse_duration("0h0mi") == 0

def test_junk_after_valid():
    with pytest.raises(ValueError):
        parse_duration("1hxyz")

def test_junk_before_valid():
    with pytest.raises(ValueError):
        parse_duration("abc1h")