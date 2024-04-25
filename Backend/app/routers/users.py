from fastapi import Depends, FastAPI, APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import boto3
import logging
import os, sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

router = APIRouter()
app = FastAPI()

# Initialize Cognito client
cognito_client = boto3.client('cognito-idp', region_name='us-east-1')

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Users')  # Replace with your DynamoDB table name

def get_client_id():
    try:
        ssm_client = boto3.client('ssm')
        response = ssm_client.get_parameter(Name='/myapp/cognito/client_id', WithDecryption=True)
        client_id = response['Parameter']['Value']
        return client_id
    except Exception as e:
        raise Exception(f"Failed to retrieve client ID from SSM Parameter Store: {str(e)}")

def get_user_pool_id():
    try:
        ssm_client = boto3.client('ssm')
        response = ssm_client.get_parameter(Name='/myapp/cognito/user_pool_id', WithDecryption=True)
        user_pool_id = response['Parameter']['Value']
        return user_pool_id
    except Exception as e:
        raise Exception(f"Failed to retrieve user pool ID from SSM Parameter Store: {str(e)}")

USER_POOL_ID = get_user_pool_id()
CLIENT_ID = get_client_id()

class UserSignup(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

import logging

logger = logging.getLogger(__name__)

@router.post('/signup')
def signup(user_data: UserSignup):
    try:
        # Check if user already exists
        try:
            response = cognito_client.admin_get_user(
                UserPoolId=USER_POOL_ID,
                Username=user_data.email
            )
        except cognito_client.exceptions.UserNotFoundException:
            # Create user in Cognito User Pool
            response = cognito_client.sign_up(
                ClientId=CLIENT_ID,
                Username=user_data.email,
                Password=user_data.password,
                UserAttributes=[
                    {'Name': 'email', 'Value': user_data.email}
                ]
            )

            cognito_client.admin_update_user_attributes(
                UserPoolId=USER_POOL_ID,
                Username=user_data.email,
                UserAttributes=[
                    {'Name': 'email_verified', 'Value': 'true'},
                    {'Name': 'email', 'Value': user_data.email}
                ]
            )

            # Add user to DynamoDB table
            table.put_item(Item={'email': user_data.email})

            logger.info('User signed up successfully!')
            return {'message': 'User signed up successfully! Please check your email for verification.'}
        else:
            logger.info('User already exists.')
            return {'message': 'User already exists.'}
    except Exception as e:
        logger.error(f'Error during signup: {str(e)}')
        raise HTTPException(status_code=400, detail=str(e))

@router.post('/login')
def login(user_data: UserLogin):
    try:
        # Authenticate user with Cognito User Pool
        response = cognito_client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': user_data.email,
                'PASSWORD': user_data.password
            },
            ClientId=CLIENT_ID
        )

        # Extract authentication tokens
        access_token = response['AuthenticationResult']['AccessToken']
        id_token = response['AuthenticationResult']['IdToken']

        # Log successful login attempt
        logger.info(f"User '{user_data.email}' logged in successfully")

        return {'access_token': access_token, 'id_token': id_token}
    except Exception as e:
        # Log failed login attempt
        logger.error(f"Login attempt failed for user '{user_data.email}': {str(e)}")
        raise HTTPException(status_code=401, detail='Invalid credentials')

@router.post("/resend-verification")
async def resend_verification(email: str):
    try:
        response = cognito_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
            MessageAction='RESEND'
        )
        logger.info('Verification code resent successfully!')
        return JSONResponse({'message': 'Verification code resent successfully!'})
    except cognito_client.exceptions.UsernameExistsException:
        logger.error('User already exists.')
        raise HTTPException(status_code=400, detail='User already exists')
    except Exception as e:
        logger.error(f'Error during verification code resend: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/verify-email')
def verify_email(email: str, code: str):
    try:
        response = cognito_client.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=email,
            ConfirmationCode=code
        )
        logger.info('Email verification successful!')
        return {'message': 'Email verification successful! You can now sign in.'}
    except cognito_client.exceptions.UserNotFoundException:
        logger.error('User not found.')
        raise HTTPException(status_code=404, detail='User not found')
    except cognito_client.exceptions.CodeMismatchException:
        logger.error('Invalid verification code.')
        raise HTTPException(status_code=400, detail='Invalid verification code')
    except Exception as e:
        logger.error(f'Error during email verification: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))
    
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("users:app", host="0.0.0.0", port=8080, reload=True)