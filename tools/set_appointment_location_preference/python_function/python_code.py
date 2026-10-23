import re
from typing import Optional


def set_appointment_location_preference(
    at_local_store: bool, zip_code: Optional[str] = None
) -> str:
  """Sets the user's preferred location for the instore appointment.

  Args:
    at_local_store (bool): Set to True ONLY if user's preference is to
      schedule an appointment at the store they are currently calling.
    zip_code (str, optional): The 5-digit zip code to find appointments
      at nearby stores. REQUIRED if at_local_store is False.
  """
  if not at_local_store and not zip_code:
    return "zip_code is required when at_local_store is False."
  if at_local_store and not context.state.get("store_id"):
    return (
        "Ask the user for their zip code to schedule an appointment near"
        " them."
    )

  context.state["appointment_at_local_store"] = at_local_store

  if zip_code and not re.match(r"^\d{5}$", zip_code):
    return (
        f"1. Tell the user their zip code doesn't look valid and ask them for a valid one (e.g., 'The zip code {zip_code} doesn't look valid, can you please provide a valid 5 digit zip code for me to check for appointments near you?')."
        "2. Wait for the user's response."
        "3. Call this tool again with the user's updated zip code."
      )

  if zip_code:
    context.state["appointment_zip_code"] = zip_code
  return "Location preferences successfully saved."
