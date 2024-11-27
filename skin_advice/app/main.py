from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import openai
from fastapi import HTTPException
from openai import OpenAIError, Timeout
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Optional


load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()


app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)


class Probabilities(BaseModel):
   concerns: List[str]

class SkinData(BaseModel):
   probabilities: Probabilities

@app.get("/health")
async def health_check():
   return {"status": "healthy", "api_key_configured": bool(os.getenv("OPENAI_API_KEY"))}

@app.post("/get_advice")
async def get_skin_advice(skin_data: SkinData):
    print("Received skin data:", skin_data)
    concerns = skin_data.probabilities.concerns
    # concerns = skin_data.get("probabilities", {}).get("concerns", [])
    
    if concerns is None:
        print("concerns is None")
        return {"advice": "피부 상태가 전반적으로 양호합니다. 현재의 피부 관리를 유지해주세요."}


    if not concerns:
        return {"advice": "피부 상태가 전반적으로 양호합니다. 현재의 피부 관리를 유지해주세요."}


    prompt = f"""
    다음과 같은 피부 문제가 발견되었습니다:
    {', '.join(concerns)}

    이러한 피부 상태에 대한 관리 방법과 주의사항을 5줄 이내로 제안해주세요.
    피부과 전문의처럼 전문적으로 답변해주세요.
    사용자의 피부 상태에 따라 적합한 피부 관리 방법과 피해야 할 성분에 대해 간단히 설명해주세요.
    설명은5줄 이내로 요약하세요.
    사용자의 피부 상태는 JSON 형식으로 주어집니다.
    출력은 한국어로만 제공하세요.
    답변 마지막에는 반드시 한문장 내리고 "자세한 상담을 원하시면 🤖챗봇을 이용해주시기 바랍니다!"라는 문구를 추가하세요.
    """

    print("Sending request to OpenAI...")

    try:
        client = OpenAI() 
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 피부과 전문의입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        print("OpenAI response received:", response) 

        if not response or not response.choices:
            raise ValueError("Empty response from OpenAI API")

        advice = response.choices[0].message.content
        print("Received response from OpenAI:", advice)
        return {"advice": advice}

    except openai.OpenAIError as e:
        print(f"OpenAI API 오류 발생: {e}")

        if hasattr(e, 'http_body'):
            print(f"Error details: {e.http_body}")
        if hasattr(e, 'http_status'):
            print(f"HTTP status code: {e.http_status}")
    except Exception as e:
        print(f"기타 오류 발생: {e}")
if __name__ == "__main__":
   import uvicorn
   uvicorn.run(app, host="0.0.0.0", port=8000)