def play_sms_legal_disclosure() -> None:
  """Play the legal disclosure before sending the SMS."""
  context.state["played_message_data_rates_legal_disclosure"] = True
  tools.set_next_agent_actions({
      "customized_response": {
          "content": "OK, just so you know, the terms at BestBuy.com/mobile terms apply. Message and data rates may also apply. Can we text you at the number you're calling from?",
          "disable_barge_in": True,
      }
  })
