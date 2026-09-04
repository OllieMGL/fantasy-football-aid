import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import sessionmaker

from db import engine
from tools import TOOLS, TOOL_FUNCTIONS

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


def ask(user_message, player_ids):
    session = Session()

    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant inside a Fantasy Premier League team-building app. "
                "Answer the user's question about their current squad using the tools "
                "available to you. Never invent stats or scores - only state what the "
                "tools return. Keep answers short and in plain English.\n\n"
                "The user's squad may be empty or only partly built - that's a normal, "
                "valid state, not an error. For a position that's empty or short of its "
                "required count, use recommend_for_slot to suggest who to add. Only use "
                "get_recommendations' weak_player_swap_suggestions for positions that are "
                "already filled - check its squad_completeness first to see what actually "
                "needs filling versus what could just be upgraded."
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

