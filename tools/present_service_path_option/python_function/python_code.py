"""Tool that returns the presentation phrase for a given service path option."""

# pylint: disable=undefined-variable


PHRASES = {
    "Dotcom_SelfService_ServiceTriage": {
        "mail_in": (
            "We offer a convenient mail-in service that sends your device"
            " directly to a Geek Squad Service Center. Would you like more"
            " details, or would you prefer to hear about other options?"
        ),
    },
    "Dotcom_SelfService_RepairCreate_InStoreAppointment": {
        "with_store": (
            "Let's get this taken care of for you! The best option is to bring"
            " it to a Best Buy store, where our Geek Squad agents can diagnose"
            " the problem. I can help you schedule a service appointment at the"
            " {store_name} store that's convenient for you. Would you like to"
            " do that?"
        ),
        "without_store": (
            "Let's get this taken care of for you! The best option is to bring"
            " it to a Best Buy store, where our Geek Squad agents can diagnose"
            " the problem. I can help you schedule a service appointment at a"
            " location that's convenient for you. Would you like to do that?"
        ),
    },
    "Dotcom_SelfService_RemoteSupport": (
        "Our agents are capable of remotely resolving issues by establishing"
        " a secure connection to your computer. A service fee may apply for"
        " remote support sessions. Fees will be communicated upfront before"
        " any work begins. This service is free for Total members. Would you"
        " like to continue?"
    ),
    "Dotcom_SelfService_RepairDeflect": (
        "You'll need to work directly with the manufacturer for service"
        " options. You can find their contact information in your product"
        " manual or packaging. Otherwise, try searching online. You could"
        " also choose to go to an independent repair shop."
    ),
    "Dotcom_SelfService_ReturnExchange": (
        "Your item purchased on {purchased_on_date} is still returnable."
        " To start a return or exchange, you'll need to go to"
        " BestBuy.com/returns. Could we send you a one-time text message"
        " with a link to the Returns and Exchanges page?"
    ),
    "Agent": (
        "I can connect you with a live agent. Would you like to do that?"
    ),
}


def present_service_path_option(path_type: str) -> dict:
    """Returns the exact phrase to present to the user for a given service path type.

    The agent MUST say the returned phrase exactly as-is to the user, then wait
    for the user's response before proceeding.

    Args:
        path_type: The service path type from the create_and_get_service_context
            response (e.g. "Dotcom_SelfService_ServiceTriage").

    Returns:
        dict: Contains:
            - phrase (str): The exact text to say to the user.
            - requires_confirmation (bool): Whether the agent should wait for
              a yes/no response. False means the phrase is informational only
              (e.g. manufacturer deflect) and counts as auto-accepted.
    """
    init_json = context.state.get("init_json", {})
    is_mail_in_enabled = (
        str(init_json.get("mail_in_enabled", False)).lower() == "true"
    )
    store_name = context.state.get("store_name", "")
    store_id = context.state.get("store_id", "")

    requires_confirmation = True

    if path_type == "Dotcom_SelfService_ServiceTriage":
        if is_mail_in_enabled:
            phrase = PHRASES[path_type]["mail_in"]
        else:
            in_store = PHRASES["Dotcom_SelfService_RepairCreate_InStoreAppointment"]
            if store_id and store_name:
                phrase = in_store["with_store"].format(
                    store_name=store_name
                )
            else:
                phrase = in_store["without_store"]
    elif path_type == "Dotcom_SelfService_RepairCreate_InStoreAppointment":
        if store_id and store_name:
            phrase = PHRASES[path_type]["with_store"].format(
                store_name=store_name
            )
        else:
            phrase = PHRASES[path_type]["without_store"]
    elif path_type == "Dotcom_SelfService_RepairDeflect":
        phrase = PHRASES[path_type]
        requires_confirmation = False
    elif path_type == "Dotcom_SelfService_ReturnExchange":
        purchased_on_date = context.state.get("purchasedOnDate", "")
        phrase = PHRASES[path_type].format(
            purchased_on_date=purchased_on_date
        )
        context.state["should_play_return_exchange_option"] = phrase
    elif path_type in PHRASES:
        phrase = PHRASES[path_type]
    else:
        phrase = PHRASES["Agent"]

    return {
        "phrase": phrase,
        "requires_confirmation": requires_confirmation,
    }
