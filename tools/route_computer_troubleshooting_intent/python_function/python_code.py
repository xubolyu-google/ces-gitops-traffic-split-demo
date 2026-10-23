
import random

def route_computer_troubleshooting_intent(user_problem: str) -> None:
  """Handles routing of a computer troubleshooting intent.

  Args:
      user_problem (str): a summary of the user's problem, incorporating relevant details spanning the full conversation.

  Returns:
      None
  """
  context.state["user_problem"] = user_problem

  # Generate random throttle value between 0 and 1
  throttle_value = random.random()

  # Get the throttle threshold from init_json config
  # e.g., "computing_assurant_nga": "0.5" means 50% of traffic goes to new agent
  init_json = context.state.get("init_json", {})
  throttle_threshold = float(init_json.get("computing_assurant_nga", "0"))

  if throttle_value < throttle_threshold:
    # Route to the Computer Troubleshooting Assurant agent
    context.state["should_connect_to_computer_troubleshooting_assurant_agent"] = True
  else:
    # Route to the existing Computing agent
    context.state["should_connect_to_computer_troubleshooting_agent"] = True