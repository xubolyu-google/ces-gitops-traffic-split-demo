from typing import Any

def determine_price_match_action(already_purchased: bool) -> dict[str, Any]:
    """Determines the next steps for a price match request.
    
    Args:
        already_purchased (bool): True if the product was already purchased.
        
    Returns:
        dict[str, Any]: A dictionary with instructions and message for the agent.
    """
    if already_purchased:
        return {
            "instruction": "Inform the user they can submit a price match request online or in the app. Offer to connect to an agent or text a link.",
            "message": "You can submit a price match request on the Best Buy app or online under Purchases. If you prefer, I can also connect you with a live agent for more help."
        }
    else:
        return {
            "instruction": "Inform the user they can learn more about the policy online. Do NOT transfer unless explicitly asked after this message.",
            "message": "You can learn more about our price match policy online by visiting our Price Match page. Ask for an 'agent' if you need more help with Price Matching."
        }
