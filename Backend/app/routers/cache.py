from fastapi import FastAPI, Body, HTTPException, Query
from redis import Redis
from datetime import datetime
import json

app = FastAPI()

# Connect to Redis (replace with your actual connection details)
redis_client = Redis(
    host="redis-host",
    port="redis-port",
    password="redis-password"
)

@app.post("/save_chat")
async def save_chat(user_email: str = Body(...), user_message: str = Body(...), llama_message: str = Body(...)):
    """
    Save user message and llama message to Redis.
    """
    try:
        # Generate a unique key using current date and timestamp
        key = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Store user message, llama message, and timestamp as a JSON object
        data = {"user_email": user_email, "user_message": user_message, "llama_message": llama_message}
        redis_client.set(key, json.dumps(data))

        return {"message": "Chat saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving chat: {str(e)}")

@app.get("/chat_history")
async def get_chat_history(user_email: str = Query(...)):
    """
    Retrieves chat history for a specific user email from Redis.
    """
    try:
        chat_history = []
        # Iterate over all keys in Redis (optimize if performance is critical)
        for key in redis_client.scan_iter():
            data = json.loads(redis_client.get(key))
            if data["user_email"] == user_email:
                chat_history.append(data)

        if not chat_history:
            return {"message": "No chat history found for this email."}

        return {"chat_history": chat_history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")