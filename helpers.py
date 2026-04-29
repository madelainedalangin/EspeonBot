import re

MINUTES_PER_MINUTE = 1
MINUTES_PER_HOUR = 60
MINUTES_PER_DAY = 1440
MINUTES_PER_WEEK = 10080
MINUTES_PER_MONTH = 43200

MULTIPLIERS = {
  'mi': MINUTES_PER_MINUTE,
  'h': MINUTES_PER_HOUR,
  'd': MINUTES_PER_DAY,
  'w': MINUTES_PER_WEEK,
  'mo': MINUTES_PER_MONTH,
}

def parse_duration(duration: str) -> int:
  """
  Parse a duration string into total minutes. Supports single
  or combined units.

  Examples:
    "7d" -> 10080
    "1h30mi" -> 90
    "2w3d" -> 24480
    "1d12h" -> 2160

  Supported units: mi (minutes), h (hours), d (days), w (weeks), mo (months).
  Case insensitive.

  Parameter: duration, a string in the format specified above.
  Return: total number of minutes as an integer.
  """
  original = duration
  duration = duration.lower()

  pairs = re.findall(r'(\d+)(mo|mi|[dhw])', duration)

  if not pairs:
    raise ValueError(
      f"'{original}' is not a valid duration. "
      f"Example: 7d, 2w, 6mo, 1h30mi"
    )

  rebuilt = ''.join(num + unit for num, unit in pairs)
  if rebuilt != duration:
    raise ValueError(
      f"'{original}' is not a valid duration. "
      f"Example: 7d, 2w, 6mo, 1h30mi"
    )

  total = 0
  for num, unit in pairs:
    num = int(num)
    if num < 0:
      raise ValueError("Duration must be a positive number.")
    total += num * MULTIPLIERS[unit]

  return total