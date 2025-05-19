import streamlit as st
from PyPDF2 import PdfReader
import pandas as pd
import base64
import calculo_nutricional
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

USERS = {
    "mariaeduarda@email.com": "admin123",
    "gabrielgentil@email.com": "admin123",
    "luiseduardo@gmail.com": "admin123",
    "carlosmariano@gmail.com": "admin123",
    "samuelmatheus@gmail.com": "admin123"
}


# Tela de login
def login():
    st.title("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if email in USERS and USERS[email] == password:
            st.session_state['logged_in'] = True
            st.success("Login realizado com sucesso!")
        else:
            st.error("Email ou senha inválidos.")


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
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        login()
        return

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

        if st.button("Calcular calorias"):
            with st.spinner("Calculando..."):
                foods, comentario = calculo_nutricional.detect_foods(image, api_key)

                if not foods:
                    st.warning("Não foi possível identificar alimentos na foto. Tente novamente")
                else:
                    tabela = calculo_nutricional.make_table(foods)
                    st.dataframe(tabela, use_container_width=True)

                    total = calculo_nutricional.total_kcal(foods)
                    st.markdown(f"Total aproximado: **{total:.0f} kcal**")

                    if comentario:
                        st.markdown(f"**Comentário:** {comentario}")



if __name__ == "__main__":
    main()