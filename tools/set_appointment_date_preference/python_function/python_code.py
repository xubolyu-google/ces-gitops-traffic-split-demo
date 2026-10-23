from datetime import datetime

date_format = "%Y-%m-%d"


def set_appointment_date_preference(start_date: str, end_date: str) -> str:
  """Sets the user's preferred date range for an in-store appointment.

  PRE-REQUISITES:
    - You MUST only call this tool after the user has explicitly provided their
      appointment date preferences. Do not assume date preferences without
      explicitly gathering them from the user.

  Args:
    start_date (str): The inclusive start date (yyyy-mm-dd).
      - EXAMPLE: If user wants "Friday" and today is Monday 2026-03-02,
        use '2026-03-06'
    end_date (str): The exclusive end date (yyyy-mm-dd).
      - RULE: This must be the day AFTER the last day the user prefers.
      - EXAMPLE: If today is 2026-02-12 and user wants "tomorrow", use
        '2026-02-14'.
  """
  try:
    parsed_start_date = datetime.strptime(start_date, date_format)
  except ValueError as e:
    print(f"Error parsing start_date: {e}")
    return "Invalid value for start_date, should have yyyy-mm-dd format."
  try:
    parsed_end_date = datetime.strptime(end_date, date_format)
  except ValueError as e:
    print(f"Error parsing end_date: {e}")
    return "Invalid value for end_date, should have yyyy-mm-dd format."

  if parsed_start_date >= parsed_end_date:
    return "start_date must be strictly before end_date"

  context.state["appointment_start_date"] = parsed_start_date.strftime(
      date_format
  )
  context.state["appointment_end_date"] = parsed_end_date.strftime(date_format)
  return "Date preferences successfully saved."
