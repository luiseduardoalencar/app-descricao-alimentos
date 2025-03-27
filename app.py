import streamlit as st
from PyPDF2 import PdfReader
import pandas as pd
import base64
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from PIL import Image
import base64
from io import BytesIO
from datetime import datetime

def encode_image(image):
    if image.mode == 'RGBA':
        image = image.convert('RGB')  
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def describe_image(image, api_key):
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
    encoded_image = encode_image(image)

    prompt = "Descreva em detalhes a imagem enviada:"

    response = model.invoke(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{encoded_image}"}
                ],
            }
        ]
    )

    return response.content

def main():
    st.set_page_config(page_title="App de descrição de imagem", page_icon=":camera:")
    st.title("📷 App para descrição de imagem")

    api_key = st.sidebar.text_input("Insira a sua chave api do Gemini:", type="password")

    if not api_key:
        st.sidebar.warning("Por favor, insira sua chave API do Gemini para prosseguir.")
        return

    uploaded_file = st.file_uploader("Faça o upload de uma imagem (PNG or JPEG):", type=["png", "jpeg", "jpg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagem carregada", use_container_width=True)

        if st.button("Gerar descrição"):
            with st.spinner("Gerando descrição..."):
                description = describe_image(image, api_key)
                st.success("Descrição gerada!")
                st.write(description)

if __name__ == "__main__":
    main()