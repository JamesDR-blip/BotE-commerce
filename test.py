import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Sử dụng chính xác mã ID từ danh sách bạn vừa chụp
llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash" 
)

try:
    response = llm.invoke("Xin chào Gemini 3.6, kết nối qua LangChain đã chạy được chưa?")
    print("🎉 KẾT NỐI THÀNH CÔNG!")
    print(f"Phản hồi từ AI: {response.content}")
except Exception as e:
    print(f"❌ Lỗi: {e}")
