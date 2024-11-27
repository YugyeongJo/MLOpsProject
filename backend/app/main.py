from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
import os

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

MODEL_ENDPOINTS = {
    "skin_type": "http://skin_type:8000/predict",
    "skin_flushing": "http://skin_flushing:8000/predict",
    "skin_wrinkle": "http://skin_wrinkle:8000/predict",
    "skin_pores": "http://skin_pores:8000/predict",
    "skin_defect": "http://skin_defect:8000/predict"
}

ADVICE_ENDPOINT = "http://skin_advice:8000/get_advice"
CHATBOT_URL = os.getenv('CHATBOT_URL', 'http://chatbot:8000')

async def get_prediction(client: httpx.AsyncClient, url: str, image: bytes):
    files = {"file": ("image.jpg", image, "image/jpeg")}
    response = await client.post(url, files=files)
    result = response.json()
    

    if url == MODEL_ENDPOINTS["skin_defect"]:
        print("Skin defect response:", result)
        return {
            "file_name": result.get("file_name"),
            "predictions": result.get("predictions", []),  
            "image": result.get("image"),           
            "message": result.get("message")
        }
    return result

async def get_skin_advice(client: httpx.AsyncClient, analysis_results: dict):
    try:
        print("Sending data to skin_advice:", analysis_results)
        concerns = []
       
        skin_type_probs = analysis_results.get("skin_type_analysis", {}).get("probabilities", {})
        print("Skin type probabilities:", skin_type_probs)
        
        print("Flushing analysis:", analysis_results.get("skin_flushing_analysis"))
        print("Pores analysis:", analysis_results.get("skin_pores_analysis"))
        print("Wrinkle analysis:", analysis_results.get("skin_wrinkle_analysis"))
        print("Defect analysis:", analysis_results.get("skin_defect_analysis"))
        if skin_type_probs:
            max_type = max(skin_type_probs.items(), key=lambda x: x[1])
            concerns.append(f"피부 타입: {max_type[0]}")
        
        if analysis_results.get("skin_flushing_analysis", {}).get("prediction") == "flushing":
            concerns.append("홍조")
        
        if analysis_results.get("skin_pores_analysis", {}).get("prediction") == "pores":
            concerns.append("모공 문제")
       
        if analysis_results.get("skin_wrinkle_analysis", {}).get("prediction") == "wrinkle":
            concerns.append("주름")
        
        defect_data = analysis_results.get("skin_defect_analysis", {})
        if defect_data.get("predictions"):
            defect_types = set()  
            for prediction in defect_data["predictions"]:
                if prediction.get("category"):
                    if prediction["category"] == "psoriasis":
                        defect_types.add("건선")
                    elif prediction["category"] == "pigmentation":
                        defect_types.add("색소침착")
                    elif prediction["category"] == "acne":
                        defect_types.add("여드름")
            
            for defect_type in defect_types:
                concerns.append(f"피부 결함: {defect_type}")

        skin_data = {
            "probabilities": {
                "concerns": concerns
            }
        }

        try:
            print(f"Attempting to connect to advice service at {ADVICE_ENDPOINT}")
            print("Request data:", skin_data)
            
            response = await client.post(
                ADVICE_ENDPOINT,
                json=skin_data,
                timeout=30.0,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print("Raw response content:", response.content)
            result = response.json()
            print("Raw advice service response:", result)
            
            if response.status_code != 200:
                print(f"Non-200 status code: {response.status_code}")
                return {
                    "advice": f"서버 응답 오류 ({response.status_code})"
                }
            
            if not result:
                print("Empty response from advice service")
                return {
                "advice": "조언 서비스로부터 응답을 받지 못했습니다."
                }
                
            if "error" in result:
                print(f"Error in response: {result['error']}")
                return {
                    "advice": result.get("error")
                }
            
            if "advice" not in result:
                print("No advice in response")
                return {
                    "advice": "조언 생성에 실패했습니다."
                }
            
            return {"advice": result["advice"]}
            
        except httpx.TimeoutException as e:
            print(f"Timeout error: {str(e)}")
            return {
                "advice": "조언 생성 시간이 초과되었습니다. 다시 시도해주세요."
            }
        except httpx.ConnectError as e:
            print(f"Connection error: {str(e)}")
            return {
                "advice": "조언 서비스 연결 실패. 서버 상태를 확인해주세요."
            }
        except httpx.HTTPError as e:
            print(f"HTTP error: {str(e)}")
            return {
                "advice": f"HTTP 오류: {str(e)}"
            }
        except Exception as e:
            print(f"Unexpected error in advice request: {str(e)}")
            print(f"Error type: {type(e)}")
            return {
                "advice": f"예상치 못한 오류 발생: {str(e)}"
            }

    except Exception as e:
        print(f"Top-level error in get_skin_advice: {str(e)}")
        print(f"Error type: {type(e)}")

        print("analysis_results:", analysis_results)
        print("ADVICE_ENDPOINT:", ADVICE_ENDPOINT)
    
        import traceback
        print("Stack trace:", traceback.format_exc())
        return {
            "advice": f"전체 처리 중 오류 발생: {str(e)}"
        }
    

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    try:
        image_data = await file.read()
        
        async with httpx.AsyncClient() as client:
            tasks = []
            for service_name, url in MODEL_ENDPOINTS.items():
                task = get_prediction(client, url, image_data)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)

            skin_defect_result = results[4]
            if isinstance(skin_defect_result, Exception):
                print(f"Skin defect error: {str(skin_defect_result)}")
                skin_defect_result = {"error": str(skin_defect_result)}
            else:
                print("Skin defect success:", skin_defect_result)
            
            response = {
                "file_name": file.filename,
                "skin_type_analysis": results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])},
                "skin_flushing_analysis": results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])},
                "skin_wrinkle_analysis": results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])},
                "skin_pores_analysis": results[3] if not isinstance(results[3], Exception) else {"error": str(results[3])},
                "skin_defect_analysis": skin_defect_result,
                "message": "Analysis completed"
            }
            
            try:
                advice_result = await get_skin_advice(client, response)
                response["skin_advice"] = advice_result
            except Exception as e:
                response["skin_advice"] = {"error": str(e)}
            
            response["message"] = "Analysis completed"
            return JSONResponse(content=response)
            
    except Exception as e:
        return JSONResponse(
            content={
                "file_name": file.filename,
                "message": f"Error: {str(e)}",
                "error": True
            },
            status_code=500
        )
    
@app.post("/chat")
async def chat_endpoint(message: dict):
    try:
        print(f"Connecting to chatbot at: {CHATBOT_URL}/chat")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CHATBOT_URL}/chat",
                json={"message": message.get("message")}, 
                timeout=30.0,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Chatbot service error: {response.status_code}")
                print(f"Response content: {response.content}")
                return {"error": "챗봇 서비스 오류가 발생했습니다."}
            
    except Exception as e:
        print(f"Chat error detail: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {"error": f"오류가 발생했습니다: {str(e)}"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}