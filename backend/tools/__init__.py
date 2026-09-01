# Combines every individual tool file into the two things ai_assistant.py needs:
# a list of schemas to send to the model, and a name -> function lookup to
# dispatch with. ai_assistant.py doesn't need to know how many tools exist or
# what's in each file - just that these two things exist. Adding a new tool
# means writing one new file below and adding two lines here.

from tools.team_score import TOOL_SCHEMA as team_score_schema, call_get_team_score
from tools.slot_recommendation import TOOL_SCHEMA as slot_recommendation_schema, call_recommend_for_slot
from tools.team_recommendations import TOOL_SCHEMA as team_recommendations_schema, call_get_recommendations

TOOLS = [
    team_score_schema,
    slot_recommendation_schema,
    team_recommendations_schema,
]

TOOL_FUNCTIONS = {
    "get_team_score": call_get_team_score,
    "recommend_for_slot": call_recommend_for_slot,
    "get_recommendations": call_get_recommendations,
}
