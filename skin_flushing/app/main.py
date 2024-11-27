from fastapi import FastAPI, File, UploadFile 
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import torch
import torchvision.transforms as transforms
import torch.nn.functional as F
from torchvision import models
from PIL import Image
import torch.nn as nn
import torchvision
import shutil
import os
from typing import Dict
from pydantic import BaseModel 
# 
# from my_back.models_predict import SkinPredictor
# from my_back.schemas.response import PredictionResponse
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

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


categories = ['normal', 'flushing']

class VGG16Model(nn.Module):
    def __init__(self, num_classes):
        super(VGG16Model, self).__init__()
        self.backbone = models.vgg16(pretrained=True)
        for param in self.backbone.features.parameters():
            param.requires_grad = False

        self.backbone.classifier = nn.Sequential(
            nn.Linear(25088, 4096),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.5),
            nn.Linear(4096, 2048),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.4),
            nn.Linear(2048, num_classes)
        )

        for m in self.backbone.classifier.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        return self.backbone(x)

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# def predict_image(model, image_path, transform, categories, temperature=1):
#     image = Image.open(image_path).convert('RGB')
#     image = transform(image).unsqueeze(0)
#     image = image.to(device)

#     model.eval()
#     with torch.no_grad():
#         output = model(image)


#         logits = torch.log(torch.abs(output) + 1)


#         scaled_logits = logits / temperature
#         probabilities = torch.nn.functional.softmax(scaled_logits, dim=1)[0]


#         probabilities = torch.clamp(probabilities, min=0.01, max=0.99)
#         probabilities = probabilities / probabilities.sum()

#         class_probabilities = {
#             category: float(probabilities[idx] * 100)
#             for idx, category in enumerate(categories)
#         }

#         sorted_probabilities = dict(sorted(class_probabilities.items(),
#                                          key=lambda x: x[1],
#                                          reverse=True))

#         print("\n피부 타입 분석 결과:")
#         for skin_type, prob in sorted_probabilities.items():
#             print(f'{skin_type}: {prob:.2f}%')

#     return sorted_probabilities

class PredictionResponse(BaseModel):
    file_name: str
    prediction: str
    probabilities: Dict[str, float]
    message: str

model = VGG16Model(num_classes=len(categories)).to(device)
model.load_state_dict(torch.load('model/best_vgg18_model_flushing.pth', map_location=device))
model.eval()


@app.post("/predict", response_model=PredictionResponse)
async def upload_file(file: UploadFile = File(...)):
    try:
        temp_file = f"temp_{file.filename}"
        with open(temp_file, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            image = Image.open(temp_file).convert('RGB')
            image_tensor = transform(image).unsqueeze(0).to(device)
            
            model.eval()
            with torch.no_grad():
                output = model(image_tensor)
                
  
                temperature = 2.0
                scaled_logits = output / temperature
                probabilities = F.softmax(scaled_logits, dim=1)[0]

    
                flushing_prob = float(probabilities[0] * 100)
                normal_prob = float(probabilities[1] * 100)

     
                class_probabilities = {
                    "flushing": round(flushing_prob, 1),
                    "normal": round(normal_prob, 1)
                }


                print("\n피부 홍조 분석 결과:")
                if flushing_prob > normal_prob:
                    prediction = "flushing"
                    print("홍조가 있습니다.")
                else:
                    prediction = "normal"
                    print("홍조가 없습니다.")
                print(f"확률: 홍조 {flushing_prob:.1f}% / 정상 {normal_prob:.1f}%")

                result = {
                    "file_name": file.filename,
                    "prediction": prediction,
                    "probabilities": class_probabilities,
                    "message": "분석 완료"
                }
                
                print("Sending response:", result)
                return JSONResponse(content=result)
            
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return JSONResponse(
            content={
                "file_name": file.filename if file else "unknown",
                "prediction": "unknown",
                "probabilities": {
                    "flushing": 0.0,
                    "normal": 0.0
                },
                "message": f"Error: {str(e)}"
            },
            status_code=500
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}