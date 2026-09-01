import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import sessionmaker

from db import engine
from team_scorer import get_players_by_ids, score_team, check_valid_team


# DeepSeek picks the right tool 
# → scoring algorithm runs against database 
# → DeepSeek phrases the real result in plain English
load_dotenv()

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

Session = sessionmaker(bind=engine)

MODEL = "deepseek-v4-flash"  


# ---------------------------------------------------------------------------
# Tool 1: get_team_score
#
# This is the description of the function that gets sent to the model - it's
# metadata, not code. The model reads this and decides WHETHER and WHEN to call
# it; it never runs anything itself. "parameters" is empty because the model
# doesn't need to tell us anything here - it doesn't know (and doesn't need to
# know) which players are in the squad. We already know that from the request,
# so we supply player_ids ourselves down in call_get_team_score, not the model.
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_team_score",
            "description": (
                "Calculates the user's current squad's overall score out of 100, "
                "using the app's own weighted scoring algorithm across all 15 players."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }
]


def call_get_team_score(player_ids, session):
    """The real work - runs the app's actual scoring logic against the actual database.
    This is the function the schema above is just describing to the model."""

    team_players = get_players_by_ids(player_ids, session)
    errors = check_valid_team(team_players)

    if errors:
        return {"error": " ".join(errors)}

    score = score_team(player_ids, session)
    return {"score": score}


# maps a tool name the model can ask for -> the real Python function that does it
TOOL_FUNCTIONS = {
    "get_team_score": call_get_team_score,
}


def ask(user_message, player_ids):
    session = Session()

    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant inside a Fantasy Premier League team-building app. "
                "Answer the user's question about their current squad using the tools "
                "available to you. Never invent stats or scores - only state what the "
                "tools return. Keep answers short and in plain English."
            ),
        },
        {"role": "user", "content": user_message},
    ]

    response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
    message = response.choices[0].message

    # the model can ask for a tool, get the result, and ask for another tool before
    # it's ready to answer in words - so this keeps going until it stops asking
    while message.tool_calls:
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
                for call in message.tool_calls
            ],
        })

        for call in message.tool_calls:
            function = TOOL_FUNCTIONS[call.function.name]
            arguments = json.loads(call.function.arguments)  # the model sends args back as a JSON string
            result = function(player_ids=player_ids, session=session, **arguments)

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,  # links this result back to the specific call that asked for it
                "content": json.dumps(result),
            })

        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        message = response.choices[0].message

    session.close()
    return message.content


def main():
    player_ids = [496, 418, 4, 142, 423, 154, 557, 397, 427, 165, 411, 497, 539, 212, 272]

    reply = ask("How good is my current team?", player_ids)
    print(reply)


if __name__ == "__main__":
    main()


