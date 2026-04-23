def parse_duration(duration: str) -> int:
  """
  This function takes a string in the format of the following:
  "3d"
  "3D"
  "3w"
  "3W"
  "5mi"
  "5MI"
  "5Mi"
  "5mI"
  "4mO"
  "4mo"
  "4MO"
  "4Mo"
  and splits the number from the letter. The letter d is unit for day,
  w for weeks, mi for minutes and mo for months. The number, previously a string 
  is converted to an integer and gets multiplied according to the unit. The 
  units remain case insensitive as well.
  
  Parameter: duration, a string in the format specified above.
  Return: total number of minutes as an integer, an int
  """
  
  duration = duration.lower()
  unit = duration[-1:]
  
  if unit == 'o' or unit == 'i':
    unit = duration[-2:]
    num = int(duration[:-2])
    if num < 0:
      raise ValueError("Duration must be a positive number.")
  else:
    num = int(duration[:-1])
    if num < 0:
      raise ValueError("Duration must be a positive number.")

  if unit == 'mi':
    minutes = num * 1
    return minutes
  
  elif unit == 'h':
    hours = num * 60
    return hours
  
  elif unit == 'w':
    weeks = num * 10080
    return weeks

  elif unit == 'd':
    days = num * 1440
    return days
  
  elif unit == 'mo':
    months = num * 43200
    return months
  
  else:
    raise ValueError(f"Unknown unit '{unit}'. Use mi (minutes), h (hours), d (days), w (weeks), mo (months).")