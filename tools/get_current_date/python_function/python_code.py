import datetime
from zoneinfo import ZoneInfo


def get_current_date() -> str:
  """Get the current date."""
  mock = context.state.get("mock_date")
  if mock:
    return mock

  LA_timezone = ZoneInfo("America/Los_Angeles")
  return datetime.datetime.now(LA_timezone).strftime("%a, %d %b %Y")
