import streamlit as st
import pandas as pd
import base64
import calculo_nutricional
from langchain_google_genai import ChatGoogleGenerativeAI
from PIL import Image
from io import BytesIO
from gtts import gTTS

# --- Page Configuration ---
st.set_page_config(page_title="App de descrição de imagem", page_icon=":camera:", layout="wide")

# --- User Data ---
USERS = {
    "mariaeduarda@email.com": "admin123",
    "gabrielgentil@email.com": "admin123",
    "luiseduardo@gmail.com": "admin123",
    "carlosmariano@gmail.com": "admin123",
    "samuelmatheus@gmail.com": "admin123"
}

# --- Helper Functions ---
def login():
    with st.container():
        st.title("🔐 Login")
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Senha", type="password", key="login_password")
            if st.session_state.get('login_attempted_error', False):
                st.error("Email ou senha inválidos.")
                st.session_state.login_attempted_error = False
            if st.button("Entrar", key="login_button", use_container_width=True):
                if email in USERS and USERS[email] == password:
                    st.session_state['logged_in'] = True
                    st.session_state.pop('login_attempted_error', None)
                    st.rerun() # CORREÇÃO AQUI
                else:
                    st.session_state['logged_in'] = False
                    st.session_state.login_attempted_error = True
                    st.rerun() # CORREÇÃO AQUI

def encode_image(image: Image.Image) -> str:
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def describe_image(image: Image.Image, api_key: str) -> str:
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
    return response.content if response and hasattr(response, 'content') else "Não foi possível gerar a descrição."

def text_to_speech_bytes(text: str, lang: str = 'pt-br') -> BytesIO | None:
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return audio_fp
    except Exception as e:
        st.error(f"Erro ao gerar áudio: {e}")
        return None

def format_table_for_speech(df_table: pd.DataFrame) -> str:
    if df_table is None or df_table.empty:
        return "Nenhuma tabela de alimentos para ler."
    speech_text = "A tabela de alimentos é a seguinte: "
    for index, row in df_table.iterrows():
        alimento = row.get("Alimento", "Alimento não especificado")
        porcao = row.get("Porção", "porção não especificada") 
        kcal_100g = row.get("kcal / 100 g", "calorias não especificadas")
        if isinstance(kcal_100g, (int, float)):
            kcal_text = f"{kcal_100g:.0f} quilocalorias por 100 gramas"
        elif kcal_100g == "–":
            kcal_text = "quilocalorias não disponíveis por 100 gramas"
        else:
            kcal_text = f"{kcal_100g} por 100 gramas"
        speech_text += f"{alimento}, porção {porcao}, {kcal_text}. "
    return speech_text

def initialize_session_state():
    defaults = {
        'logged_in': False,
        'login_attempted_error': False,
        'description_text': None,
        'nutritional_comment_text': None,
        'foods_data': None,
        'total_kcal_data': None,
        'api_key_valid': True,
        'uploaded_image_bytes': None,
        'current_file_uploader_key': "file_uploader_initial"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def clear_all_results():
    st.session_state.description_text = None
    st.session_state.nutritional_comment_text = None
    st.session_state.foods_data = None
    st.session_state.total_kcal_data = None

def clear_image_and_results():
    clear_all_results()
    st.session_state.uploaded_image_bytes = None
    st.session_state.current_file_uploader_key = f"file_uploader_{pd.Timestamp.now().timestamp()}"
    st.rerun() # CORREÇÃO AQUI


# --- Main Application Logic ---
def main_app_content():
    st.title("📷 App para descrição de imagem")
    
    with st.sidebar:
        st.header("Configurações e Imagem")
        api_key = st.text_input("Insira a sua chave API do Gemini:", type="password", key="api_key_input")

        if not api_key:
            st.warning("Por favor, insira sua chave API do Gemini para prosseguir.")
            if st.session_state.api_key_valid:
                clear_all_results()
            st.session_state.api_key_valid = False
        else:
            st.session_state.api_key_valid = True

        st.markdown("---")

        uploaded_file = st.file_uploader(
            "Faça o upload de uma imagem (PNG or JPEG):",
            type=["png", "jpeg", "jpg"],
            key=st.session_state.current_file_uploader_key,
            on_change=clear_all_results 
        )

        if uploaded_file is not None:
            new_image_bytes = uploaded_file.getvalue()
            if st.session_state.uploaded_image_bytes != new_image_bytes:
                 st.session_state.uploaded_image_bytes = new_image_bytes
                 clear_all_results()

            if st.session_state.uploaded_image_bytes:
                try:
                    st.image(st.session_state.uploaded_image_bytes, caption="Imagem carregada", use_container_width=True)
                    if st.button("Limpar Imagem e Resultados", key="btn_clear_image_sidebar", use_container_width=True):
                        clear_image_and_results()
                except Exception as e:
                    st.error(f"Erro ao exibir a imagem: {e}")
                    st.session_state.uploaded_image_bytes = None
        elif st.session_state.uploaded_image_bytes:
             st.session_state.uploaded_image_bytes = None


    if not st.session_state.api_key_valid:
        st.info("Por favor, insira uma chave API válida na barra lateral para continuar.")
        return

    if not st.session_state.uploaded_image_bytes:
        st.info("Por favor, faça o upload de uma imagem na barra lateral para análise.")
        return

    try:
        image_for_processing = Image.open(BytesIO(st.session_state.uploaded_image_bytes))
    except Exception as e:
        st.error(f"Não foi possível processar a imagem carregada: {e}")
        return

    tab1_desc, tab2_nutrition = st.tabs(["ℹ️ Descrição da Imagem", "🥗 Análise Nutricional"])

    with tab1_desc:
        st.subheader("Gerar Descrição Detalhada")
        if st.button("Gerar descrição textual", key="btn_gerar_descricao_textual", use_container_width=True):
            with st.spinner("Gerando descrição..."):
                try:
                    description = describe_image(image_for_processing, api_key)
                    st.session_state.description_text = description
                except Exception as e:
                    st.error(f"Erro ao gerar descrição: {e}")
                    st.session_state.description_text = None
        
        if st.session_state.description_text:
            st.write(st.session_state.description_text)
            if st.button("Ouvir Descrição", key="btn_ouvir_descricao_tab", help="Clique para ouvir a descrição"):
                audio_bytes = text_to_speech_bytes(st.session_state.description_text)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")

    with tab2_nutrition:
        st.subheader("Calcular Informações Nutricionais")
        if st.button("Analisar Alimentos e Calorias", key="btn_calcular_calorias_tab", use_container_width=True):
            with st.spinner("Calculando..."):
                try:
                    foods, comentario = calculo_nutricional.identificar_comida(image_for_processing, api_key)
                    st.session_state.nutritional_comment_text = comentario

                    if not foods:
                        st.warning("Não foi possível identificar alimentos na foto. Tente novamente")
                        st.session_state.foods_data = pd.DataFrame()
                        st.session_state.total_kcal_data = None
                    else:
                        tabela_df = calculo_nutricional.criar_tabela(foods)
                        st.session_state.foods_data = tabela_df
                        total = calculo_nutricional.total_kcal(foods)
                        st.session_state.total_kcal_data = total
                except Exception as e:
                    st.error(f"Erro ao calcular calorias: {e}")
                    st.session_state.nutritional_comment_text = None
                    st.session_state.foods_data = pd.DataFrame()
                    st.session_state.total_kcal_data = None

        if st.session_state.foods_data is not None and not st.session_state.foods_data.empty:
            st.markdown("##### Tabela Nutricional")
            st.dataframe(st.session_state.foods_data, use_container_width=True)
            if st.button("Ouvir Tabela Nutricional", key="btn_ouvir_tabela_tab", help="Clique para ouvir os detalhes"):
                table_speech_text = format_table_for_speech(st.session_state.foods_data)
                audio_bytes_table = text_to_speech_bytes(table_speech_text)
                if audio_bytes_table:
                    st.audio(audio_bytes_table, format="audio/mp3")
        
        if st.session_state.total_kcal_data is not None:
            total_kcal_text = f"Total aproximado: {st.session_state.total_kcal_data:.0f} quilocalorias"
            st.markdown(f"**{total_kcal_text}**")
            if st.button("Ouvir Total de Calorias", key="btn_ouvir_total_kcal_tab", help="Clique para ouvir o total"):
                audio_bytes_total_kcal = text_to_speech_bytes(total_kcal_text)
                if audio_bytes_total_kcal:
                    st.audio(audio_bytes_total_kcal, format="audio/mp3")

        if st.session_state.nutritional_comment_text:
            st.markdown("##### Comentário Nutricional")
            st.markdown(f"{st.session_state.nutritional_comment_text}")
            if st.button("Ouvir Comentário", key="btn_ouvir_comentario_tab", help="Clique para ouvir o comentário"):
                audio_bytes_comment = text_to_speech_bytes(st.session_state.nutritional_comment_text)
                if audio_bytes_comment:
                    st.audio(audio_bytes_comment, format="audio/mp3")

def main():
    initialize_session_state()
    if not st.session_state['logged_in']:
        login()
    else:
        main_app_content()

if __name__ == "__main__":
    main()