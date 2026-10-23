from typing import Any

def check_order_actionability(action_type: str) -> dict[str, Any]:
    """Checks if the active order can be cancelled or modified and returns instructions.

    Args:
        action_type (str): The action to check, either 'cancel' or 'modify'.

    Returns:
        dict[str, Any]: A dictionary with actionability results and instructions.
    """
    order_id = context.state.get("order_id")
    if not order_id:
        return _handle_error("No order_id set in session state. Call set_order_id first.")

    orders_by_id = context.state.get("orders_by_id", {})
    
    if not orders_by_id:
        return _handle_error("No orders cached in session state.")
        
    order = orders_by_id.get(order_id)
    
    if not order:
        return _handle_error(f"Order with ID {order_id} not found in cache.")
        
    item_stats = order.get("itemStats", {})
    
    if action_type == "cancel":
        cancellable_count = int(item_stats.get("cancellableCount", 0))
        total_count = int(item_stats.get("totalCount", 0))
        store_pickup_count = int(item_stats.get("storePickupCount", 0))
        ship_to_home_count = int(item_stats.get("shipToHomeCount", 0))
        
        if cancellable_count > 0:
            return {
                "is_cancellable": True,
                "message": "Your order can still be cancelled online.",
                "instruction": "Direct user to BestBuy.com/orders to cancel."
            }
        elif cancellable_count == 0:
            if total_count == store_pickup_count and total_count > 0:
                return {
                    "is_cancellable": False,
                    "message": "Since this is a store pickup order, you can simply choose not to pick the items up. The order will be automatically cancelled 7 days after you placed it.",
                    "instruction": "Inform user they can just not pick up."
                }
            elif total_count == ship_to_home_count and total_count > 0:
                return {
                    "is_cancellable": False,
                    "message": "Your order is already shipped, so you can no longer cancel it. Once you receive it, you can choose to return it at a local Best Buy store or by using the prepaid return label.",
                    "instruction": "Inform user order is shipped and must be returned."
                }
            else:
                return {
                    "is_cancellable": False,
                    "message": "I cannot determine if this order can be cancelled. Please check online.",
                    "instruction": "Direct user to BestBuy.com/orders."
                }
                
    elif action_type == "modify":
        # Check modification permission flags in itemStats
        modify_ship_to = int(item_stats.get("modifyShipToAddressAllowedCount", 0))
        modify_pickup = int(item_stats.get("modifyPickupLocationAllowedCount", 0))
        
        if modify_ship_to > 0 or modify_pickup > 0:
             return {
                 "is_modifiable": True,
                 "message": "Any order changes should be done on BestBuy.com/orders or in our mobile app.",
                 "instruction": "Direct user to BestBuy.com/orders to modify."
             }
        else:
             return {
                 "is_modifiable": False,
                 "message": "We're sorry, but no changes can be made to your order at this time. If you receive an item you don't want, you can choose to return it at a local Best Buy store or by using the prepaid return label available on the order details page.",
                 "instruction": "Inform user no changes can be made."
             }
             
    else:
        return _handle_error(f"Invalid action_type: {action_type}")

def _handle_error(error_message: str) -> dict[str, Any]:
    context.state["check_order_actionability_failure"] = error_message
    print(f"ERROR: check_order_actionability failed: {error_message}")
    return {}
