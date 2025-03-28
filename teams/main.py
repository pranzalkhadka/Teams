from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext, MessageFactory
from botbuilder.schema import Activity, ActivityTypes
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME')
APP_ID = os.getenv('APP_ID')
APP_PASSWORD = os.getenv('APP_PASSWORD')


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = BotFrameworkAdapterSettings(app_id=APP_ID, app_password=APP_PASSWORD)
adapter = BotFrameworkAdapter(settings)

def generate_response(user_text: str) -> str:
    try:
        chat = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=MODEL_NAME)
        response = chat.invoke([HumanMessage(content=user_text)])
        return response.content
    except Exception as e:
        return f"Error: {str(e)}"

async def on_turn(turn_context: TurnContext):
    if turn_context.activity.type == ActivityTypes.message:
        user_text = turn_context.activity.text
        response_text = generate_response(user_text)
        await turn_context.send_activity(MessageFactory.text(response_text))
    elif turn_context.activity.type == ActivityTypes.conversation_update:
        if turn_context.activity.members_added:
            for member in turn_context.activity.members_added:
                if member.id != turn_context.activity.recipient.id:
                    await turn_context.send_activity("Hello! How can I assist you today?")
    else:
        await turn_context.send_activity("I only respond to messages!")

@app.get("/")
async def root():
    return {"message": "Teams Chatbot API is running"}

@app.post("/api/messages")
async def messages(request: Request):
    try:
        body = await request.json()
        
        activity = Activity().deserialize(body)

        auth_header = request.headers.get("Authorization", "")
        await adapter.process_activity(activity, auth_header, on_turn)

        return {}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))