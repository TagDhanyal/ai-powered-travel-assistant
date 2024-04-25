import logging
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import boto3
from fastapi.routing import APIRouter

app = FastAPI()

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Users')  # Replace with your DynamoDB table name

class UserPreferences(BaseModel):
    email: str
    preferences: list

@app.post("/preference_save")
def save_preferences(user_preferences: UserPreferences):
    try:
        # Update preferences in DynamoDB
        response = table.update_item(
            Key={'email': user_preferences.email},
            UpdateExpression='SET preferences = :val',
            ExpressionAttributeValues={':val': user_preferences.preferences},
            ReturnValues='UPDATED_NEW'
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/preferences")
def get_preferences(email: str = Query(..., title="User Email")):
    try:
        logging.debug(f"Received GET request for email: {email}")

        # Get preferences from DynamoDB
        response = table.get_item(Key={'email': email})
        preferences = response.get('Item', {}).get('preferences')
        if preferences:
            return {'preferences': preferences}
        else:
            logging.error("Preferences not found")
            return {'message': 'User has no preferences'}, 404
    except Exception as e:
        logging.exception("An error occurred in get_preferences")
        raise HTTPException(status_code=500, detail=str(e))

router = APIRouter()
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("preferences:app", host="0.0.0.0", port=8081, reload=True)