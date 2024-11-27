import os
import openai
import faiss
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import torch
from dotenv import load_dotenv
from transformers import ElectraTokenizer, ElectraModel
from pydantic import BaseModel


load_dotenv()
app = FastAPI()

origins = [
   "http://localhost:3000",
   "http://localhost:8000",
   "http://127.0.0.1:3000",
   "http://127.0.0.1:8000",
   "http://frontend:3000",  
]

app.add_middleware(
   CORSMiddleware,
   allow_origins=origins,
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
   expose_headers=["*"],
)


openai.api_key = os.getenv("OPENAI_API_KEY")

tokenizer = ElectraTokenizer.from_pretrained("monologg/koelectra-base-v3-discriminator")
model = ElectraModel.from_pretrained("monologg/koelectra-base-v3-discriminator")


def load_faiss_index(index_file):
   try:
       index = faiss.read_index(index_file)
       return index
   except Exception as e:
       print(f"Error loading FAISS index: {str(e)}")
       raise


def load_embeddings_and_documents(embedding_file):
   try:
       embeddings = []
       documents = []
       with open(embedding_file, 'r', encoding='utf-8') as f:
           for line in f:
               parts = line.strip().split('\t')
               documents.append(parts[1])  
               embeddings.append(np.array([float(x) for x in parts[0].split()], dtype=np.float32))  # 임베딩 벡터
       return np.array(embeddings), documents
   except Exception as e:
       print(f"Error loading embeddings: {str(e)}")
       raise


def generate_query_embedding(query, tokenizer, model):
   inputs = tokenizer(query, return_tensors='pt', truncation=True, padding=True)
   with torch.no_grad():
       outputs = model(**inputs)
   return outputs.last_hidden_state.mean(dim=1).numpy()  


def search_similar_documents(query, faiss_index, embeddings, documents, tokenizer, model, k=5):

   query_embedding = generate_query_embedding(query, tokenizer, model)
   

   _, indices = faiss_index.search(query_embedding, k) 
   

   similar_documents = [documents[i] for i in indices[0]]
   
   return similar_documents


def generate_answer_with_gpt(query, similar_documents):
   prompt = f"Here are some documents that might help answer the question:\n\n"
   prompt += "\n".join(similar_documents)  # 유사 문서들 추가
   prompt += f"\n\nQuestion: {query}\nAnswer(In Korean):"
   

   response = openai.chat.completions.create(
       model="gpt-4",  
       messages = [
            {
                "role": "system",
                "content": (
                    "피부과 전문의 역할을 맡아 답변합니다.\n"
                    "답변은 의사가 환자한테 상담해주듯 친절하게 설명하는 듯한 말투로 말해줘.\n"
                    "핵심 정보를 먼저 전달하고, 세부 설명은 나중에 합니다.\n"
                    "250토큰 이내로 답변을 완성하고,\n"
                    "마지막 50토큰은 문장을 마무리하는 데 사용합니다.\n"
                    "모든 답변은 '궁금한 점이 더 있으시다면 말씀해 주세요.'로 끝냅니다."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
       temperature=0.7,
       max_tokens=300
   )
   
   content = response.choices[0].message.content.strip()


   if not content.rstrip().endswith(('니다.', '세요.', '요.', '.', '!')):
 
        sentences = content.split('.')
        complete_response = '. '.join(sentences[:-1]) + '.'
            

        if not complete_response.endswith("궁금한 점이 더 있으시다면 말씀해 주세요."):
            complete_response += "\n궁금한 점이 더 있으시다면 말씀해 주세요."
            
        return complete_response


   if not content.endswith("궁금한 점이 더 있으시다면 말씀해 주세요."):
        content += "\n궁금한 점이 더 있으시다면 말씀해 주세요."

   return content

class ChatMessage(BaseModel):
   message: str

@app.post("/chat")
async def chat_endpoint(chat_message: ChatMessage):
   try:
       print(f"Received message: {chat_message.message}") 
       

       faiss_index = load_faiss_index('data/faiss_index_file_koelectra_3208.index')
       embeddings, documents = load_embeddings_and_documents('data/koelectra_embeddings_3208.txt')


       similar_documents = search_similar_documents(
           chat_message.message, 
           faiss_index, 
           embeddings, 
           documents, 
           tokenizer, 
           model
       )
       

       answer = generate_answer_with_gpt(chat_message.message, similar_documents)
       print(f"Generated answer: {answer}") 
       
       return {"response": answer}
       
   except Exception as e:
       print(f"Error in chat_endpoint: {str(e)}")
       return JSONResponse(
           status_code=500,
           content={"error": f"Error generating response: {str(e)}"}
       )


@app.get("/health")
async def health_check():
   return {"status": "healthy", "api_key_configured": bool(os.getenv("OPENAI_API_KEY"))}

if __name__ == "__main__":
   import uvicorn
   uvicorn.run(app, host="0.0.0.0", port=8000)