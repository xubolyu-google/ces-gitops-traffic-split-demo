from typing import Any, Optional

NOT_INSIGNIA = """Say exactly : "We're sorry. This product can’t be serviced under factory warranty by Best Buy. You’ll need to work directly with the manufacturer.
Just a minute, while I connect you to them." and  then silently and immediately call the {@TOOL: connect_to_manufacturer_queue} tool"""

INSIGNIA = """Silently and immediately call the {@TOOL: connect_to_manufacturer_queue} tool"""

OTHER_BRANDS = """Say exactly "We're sorry. This product can’t be serviced under factory warranty by Best Buy. You’ll need to work directly with the manufacturer. You can find their contact information in your product manual or packaging. Otherwise, try searching online."
"""

def manufacturer_handoff(brand_name :str) -> str:
  """Determines the next conversational step based on user eligibility.

  The Agent MUST strictly execute the instructions returned by this tool without
  deviation.

  ### PRE-REQUISITES:
  Before calling this tool, the agent MUST have identified:
  - The `product_type` and called `set_product_info` to store it.
  - The issue `classification` ('software' or 'hardware'), and
    called `set_classification` tool to store it.

  Returns:
      str: A mandatory instruction set that the agent MUST follow to continue
        the conversation flow.
  """
  if brand_name == "Samsung":
      context.state["queue"] = "+18007267864"
      return NOT_INSIGNIA
  elif brand_name == "Lg":
      context.state["queue"] = "+18002430000"
      return NOT_INSIGNIA
  elif brand_name == "Whirlpool":
      context.state["queue"] = "+18666982538"
      return NOT_INSIGNIA    
  elif brand_name == "Insignia":
      context.state["queue"] = "SVC.HOM.______.EN.VCE.ALL"
      return INSIGNIA  
  else:
    context.state["should_transfer_to_graceful_signoff"] = True
    return OTHER_BRANDS     


