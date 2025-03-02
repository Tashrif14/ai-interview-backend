from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
import openai
import os

# Load API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Store active interview sessions
active_interviews = {}

# Request model for job details
class InterviewRequest(BaseModel):
    job_title: str
    job_description: str

@app.get("/")
def home():
    return {"message": "AI Interview Backend Running!"}

@app.post("/start_interview/")
def start_interview(request: InterviewRequest):
    prompt = f"Generate 15 job interview questions for a {request.job_title} role. Job description: {request.job_description}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}]
        )
        
        questions = response["choices"][0]["message"]["content"].split("\n")
        interview_id = len(active_interviews) + 1  # Generate interview session ID
        active_interviews[interview_id] = {"questions": questions, "index": 0}

        return {"interview_id": interview_id, "message": "Interview started! Redirecting to live conversation."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # Fixed closing parenthesis

@app.websocket("/interview/{interview_id}")
async def interview(websocket: WebSocket, interview_id: int):
    await websocket.accept()
    
    if interview_id not in active_interviews:
        await websocket.send_text("Invalid interview session.")
        await websocket.close()
        return

    session = active_interviews[interview_id]
    
    while session["index"] < len(session["questions"]):
        question = session["questions"][session["index"]]
        session["index"] += 1  # Move to next question
        
        await websocket.send_text(question)  # Send AI question
        
        # Wait for user response
        response = await websocket.receive_text()
        print(f"User response: {response}")  # Store this for feedback analysis
        
    await websocket.send_text("Interview finished. Generating feedback summary...")
    await websocket.close()
