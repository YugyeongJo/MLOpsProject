from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import torch
import cv2
import numpy as np
import os
from pathlib import Path
from typing import Dict, List
import shutil

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


MODEL_PATH = Path(__file__).parent / 'model/best_yolo_model_defect.pt' 
IMG_SIZE = 640  

class YOLOv5Detector:
    def __init__(self):
        try:
            print("Initializing YOLOv5 model...")
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', 
                                        path=str(MODEL_PATH), force_reload=True)
            self.model.conf = 0.25
            self.model.iou = 0.45
            self.categories = ['psoriasis', 'pigmentation', 'acne']
            
            if torch.cuda.is_available():
                self.model.cuda()
            print("Model initialized successfully")
                
        except Exception as e:
            print(f"Error initializing model: {str(e)}")
            raise

    def detect(self, image_path: str):
        try:
            print(f"Reading image from: {image_path}")
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Failed to read image from {image_path}")
                
            print("Running inference...")
            results = self.model(img)
            
            print("Processing results...")
            predictions = results.pandas().xyxy[0]
            
            # 결과 이미지 생성
            result_img = img.copy()
            detections = []
            for _, pred in predictions.iterrows():
                bbox = {
                    'x1': int(pred['xmin']),
                    'y1': int(pred['ymin']),
                    'x2': int(pred['xmax']),
                    'y2': int(pred['ymax'])
                }

                category = self.categories[int(pred['class'])]
                confidence = float(pred['confidence'])

                
                box_color = (107, 70, 231)
                
                cv2.rectangle(result_img, 
                            (bbox['x1'], bbox['y1']), 
                            (bbox['x2'], bbox['y2']), 
                            box_color, 2)
                
                detections.append({
                    'category': category,
                    'confidence': round(confidence * 100, 2),
                    'bbox': bbox
                })
                
            output_path = image_path.replace('.', '_result.')
            cv2.imwrite(output_path, result_img)
            
            return predictions, output_path
            
        except Exception as e:
            print(f"Error in detect method: {str(e)}")
            raise

    def detect(self, image_path: str):
        """이미지에서 피부 질환 감지"""
        try:

            original_img = cv2.imread(image_path)
            result_img = original_img.copy()
            

            results = self.model(image_path)
            predictions = results.pandas().xyxy[0]  
            
            detections = []
            

            for _, pred in predictions.iterrows():

                bbox = {
                    'x1': int(pred['xmin']),
                    'y1': int(pred['ymin']),
                    'x2': int(pred['xmax']),
                    'y2': int(pred['ymax'])
                }
                
                category = self.categories[int(pred['class'])]
                confidence = float(pred['confidence'])
                box_color = (107, 70, 231)

                cv2.rectangle(result_img, 
                            (bbox['x1'], bbox['y1']), 
                            (bbox['x2'], bbox['y2']), 
                            box_color, 2)
                

                # label = f'{category}: {confidence:.2%}'
                # cv2.putText(result_img, label, 
                #            (bbox['x1'], bbox['y1'] - 10),
                #            cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                #            (0, 255, 0), 2)
                
                detections.append({
                    'category': category,
                    'confidence': round(confidence * 100, 2),
                    'bbox': bbox
                })
            

            output_path = image_path.replace('.', '_result.')
            cv2.imwrite(output_path, result_img)
            
            return detections, output_path
            
        except Exception as e:
            print(f"감지 중 에러 발생: {str(e)}")
            raise

@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    try:
        print("1. Starting image prediction...")
        os.makedirs('uploads', exist_ok=True)
        
        file_path = f"uploads/temp_{file.filename}"
        print(f"2. Saving file to: {file_path}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            print("3. Initializing YOLOv5Detector...")
            detector = YOLOv5Detector()
            
            print("4. Running detection...")
            detections, output_path = detector.detect(file_path)
            print(f"5. Detections received: {detections}")
            print(f"6. Output path: {output_path}")
            
            print("7. Reading image file for base64 conversion...")
            with open(output_path, "rb") as img_file:
                import base64
                image_data = base64.b64encode(img_file.read()).decode()
            
            print("8. Preparing response...")
            
            response = {
                "file_name": file.filename,
                "predictions": detections,
                "image": image_data,
                "message": "분석이 완료되었습니다."
            }
            
            print("9. Sending response...")
            return JSONResponse(content=response)
            
        except Exception as e:
            print(f"Error in detection process: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise
            
        finally:
            print("10. Cleaning up temporary files...")
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(output_path):
                os.remove(output_path)
                
    except Exception as e:
        print(f"Error in main process: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return JSONResponse(
            content={
                "file_name": file.filename if file else "unknown",
                "skin_defect_analysis": {
                    "error": str(e)
                },
                "message": f"Error occurred: {str(e)}"
            },
            status_code=500
        )
@app.get("/health")
async def health_check():
    return {"status": "healthy"}