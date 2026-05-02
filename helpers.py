import re

MAX_NAME_LENGTH = 30 #good enuff
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

async def send_chunked(context, text: str, max_len = 1900) -> None:
  """
  Send a message and splitting to chunks if it exceeds the limit.

  Args:
      context: full discord message
      text: full msg to send
      max_len: Max chars per message. Defaults to 1900.
      
  Returns: None
  """
  while len(text) > max_len:
    split_index = text.rfind('\n', 0, max_len)
    if split_index == -1:
      split_index = max_len
    await context.reply(text[:split_index])
    text = text[split_index:].lstrip('\n')
  if text:
    await context.reply(text)

async def check_name(context, name):
  if name and len(name) > MAX_NAME_LENGTH:
    await context.reply(f"Name must be {MAX_NAME_LENGTH} characters or less.")
    return False
  return True