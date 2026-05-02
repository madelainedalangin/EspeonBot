import pytest
from helpers import parse_duration, MAX_NAME_LENGTH

################
# VALID INPUTS #
################

def test_days():
  assert parse_duration("7d") == 10080

def test_days_upper():
  assert parse_duration("7D") == 10080

def test_weeks():
  assert parse_duration("2w") == 20160

def test_months():
  assert parse_duration("6mo") == 259200

def test_one_day():
  assert parse_duration("1d") == 1440

def test_one_month():
  assert parse_duration("1mo") == 43200

def test_one_hour():
  assert parse_duration("1h") == 60

def test_one_minute():
  assert parse_duration("1mi") == 1

def test_one_week():
  assert parse_duration("1w") == 10080

def test_large_days():
  assert parse_duration("365d") == 525600

def test_zero_days():
  assert parse_duration("0d") == 0

def test_zero_hours():
  assert parse_duration("0h") == 0

def test_hours():
  assert parse_duration("3h") == 180

def test_minutes():
  assert parse_duration("30mi") == 30

def test_large_minutes():
  assert parse_duration("999mi") == 999

def test_large_months():
  assert parse_duration("12mo") == 518400


#####################
# COMBINED INPUTS   #
#####################

def test_hour_min():
  assert parse_duration("1h30mi") == 90

def test_day_hour():
  assert parse_duration("1d12h") == 2160

def test_week_day():
  assert parse_duration("2w3d") == 24480

def test_combined_upper():
  assert parse_duration("1H30MI") == 90

def test_three_units():
  assert parse_duration("1d2h30mi") == 1590

def test_week_day_hour():
  assert parse_duration("1w1d1h") == 11580

def test_month_week():
  assert parse_duration("1mo1w") == 53280

def test_all_units():
  assert parse_duration("1mo1w1d1h1mi") == 54781

def test_mixed_case():
  assert parse_duration("2H45Mi") == 165

def test_duplicate_units():
  assert parse_duration("1h2h") == 180

def test_zero_combined():
  assert parse_duration("0h0mi") == 0

def test_day_min():
  assert parse_duration("1d30mi") == 1470

def test_week_min():
  assert parse_duration("1w15mi") == 10095

def test_month_day():
  assert parse_duration("1mo5d") == 50400

def test_month_hour():
  assert parse_duration("1mo6h") == 43560

def test_two_weeks():
  assert parse_duration("2w") == 20160

def test_month_min():
  assert parse_duration("2mo30mi") == 86430


##################
# INVALID INPUTS #
##################

def test_bad_unit():
  with pytest.raises(ValueError, match="not a valid duration"):
    parse_duration("67x")

def test_bad_unit_y():
  with pytest.raises(ValueError, match="not a valid duration"):
    parse_duration("3y")

def test_no_number():
  with pytest.raises(ValueError):
    parse_duration("d")

def test_empty():
  with pytest.raises(Exception):
    parse_duration("")

def test_just_number():
  with pytest.raises(Exception):
    parse_duration("7")

def test_negative():
  with pytest.raises(ValueError, match="not a valid duration"):
    parse_duration("-1d")

def test_float():
  with pytest.raises(ValueError):
    parse_duration("1.5d")

def test_none():
  with pytest.raises(Exception):
    parse_duration(None)

def test_mo_typo():
  with pytest.raises(ValueError):
    parse_duration("3mx")

def test_mi_typo():
  with pytest.raises(ValueError):
    parse_duration("3mu")

def test_spaces():
  with pytest.raises(ValueError):
    parse_duration("1h 30mi")

def test_letters_only():
  with pytest.raises(ValueError):
    parse_duration("abc")

def test_junk_after():
  with pytest.raises(ValueError):
    parse_duration("1hxyz")

def test_junk_before():
  with pytest.raises(ValueError):
    parse_duration("abc1h")

def test_special_chars():
  with pytest.raises(ValueError):
    parse_duration("1h!")

def test_just_unit_mo():
  with pytest.raises(ValueError):
    parse_duration("mo")

def test_just_unit_mi():
  with pytest.raises(ValueError):
    parse_duration("mi")

def test_just_unit_h():
  with pytest.raises(ValueError):
    parse_duration("h")

def test_double_negative():
  with pytest.raises(ValueError):
    parse_duration("--1d")

def test_trailing_space():
  with pytest.raises(ValueError):
    parse_duration("1d ")

def test_leading_space():
  with pytest.raises(ValueError):
    parse_duration(" 1d")

def test_number_zero_only():
  with pytest.raises(Exception):
    parse_duration("0")

def test_emoji():
  with pytest.raises(ValueError):
    parse_duration("1d😊")


#####################
# NAME LENGTH TESTS #
#####################

def test_name_short():
  assert len("vacuum") <= MAX_NAME_LENGTH

def test_name_at_limit():
  assert len("a" * MAX_NAME_LENGTH) <= MAX_NAME_LENGTH

def test_name_over_limit():
  assert len("a" * (MAX_NAME_LENGTH + 1)) > MAX_NAME_LENGTH

def test_name_single():
  assert len("x") <= MAX_NAME_LENGTH

def test_name_with_numbers():
  assert len("cmput261") <= MAX_NAME_LENGTH

def test_name_with_hyphens():
  assert len("air-filter") <= MAX_NAME_LENGTH

def test_name_very_long():
  assert len("a" * 100) > MAX_NAME_LENGTH

def test_name_empty():
  assert len("") <= MAX_NAME_LENGTH