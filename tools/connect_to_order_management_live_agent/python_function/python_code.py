# pylint: disable=undefined-variable
from typing import Any


def connect_to_order_management_live_agent(conversation_summary: str) -> None:
  """Connects the user to an order management live agent.

  Determines the correct queue based on membership and specific issue
  conditions.
  """
  call_context = context.state.get("call_context", {})

  # Default Primary Queue
  queue = "CAR.PMY.______.EN.VCE.ALL"

  membership = context.state.get("membership")
  hotline = context.state.get("dfcx_params", {}).get("hotline")

  # Check membership for specific queues
  if membership == "Total":
    queue = "TR1.CNG.______.EN.VCE.ALL"
  elif hotline == "retail":
    queue = "TTE.SCO.______.EN.VCE.ALL"

  # Specific flows overrides
  is_large_product = context.state.get("is_large_product")
  appt_in_range = context.state.get("orderItemApptStartWithinRange")
  is_lost_late_with_photo = context.state.get("is_lost_late_with_photo")

  # TODO: "CAR.MKT.______.EN.VCE.ALL" when 3POrderEligibleForEscalation

  # TODO: Figure out the right queues for large product.
  if is_large_product:
    queue = "SUP.DOD.______.EN.VCE.ALL"  # deliver today
    queue = "SVC.HOM.______.EN.VCE.ALL"
  elif is_lost_late_with_photo:
    queue = "SUP.DOD.______.EN.VCE.ALL"

  print(
      f"INFO: Routing to queue {queue} based on membership={membership},"
      f" hotline={hotline}, is_large={is_large_product}"
  )

  call_context["queue"] = queue
  call_context["conversationSummarization"] = conversation_summary
  call_context["isSummarize"] = True

  # Set call context
  tools.set_call_context({"call_context": call_context})

  tools.set_next_agent_actions({
      "customized_response": {
          "content": "Ok, let me connect you with an agent.",
          "disable_barge_in": True,
      },
      "end_session": {"reason": "Transfer to Twilio queue"},
  })
  return None
