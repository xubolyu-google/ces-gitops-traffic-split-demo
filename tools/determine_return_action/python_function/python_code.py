from typing import Any

def determine_return_action(is_large_product: bool) -> dict[str, Any]:
    """Determines the next steps for a return inquiry involving a mix of items.
    
    Args:
        is_large_product (bool): True if it is a large product.
        
    Returns:
        dict[str, Any]: A dictionary with instructions and message for the agent.
    """
    if is_large_product:
        return {
            "instruction": "Call {@TOOL: connect_to_order_management_live_agent} with a detailed conversation summary.",
            "message": "Let me get you to an agent who can help with returning large items."
        }
    else:
        return {
            "instruction": "Inform the user immediately and do not look up orders. You MUST use the exact URL BestBuy.com/orders.",
            "message": "Ok. Looks like you have a mix of returnable and non-returnable items. For more details and to determine which items are still returnable, you'll need to go to BestBuy.com/orders."
        }
