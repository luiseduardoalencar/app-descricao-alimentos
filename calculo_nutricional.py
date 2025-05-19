import base64, json, re, requests
from io import BytesIO
from PIL import Image
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI

"""Api para cálculo nutricional:
Para fins didáticos a chave foi inserida como constante no arquivo apenas para POC"""
FDC_KEY      = "CYS9adVPPI2hVfteC5jhJBNVvc0o7fGAipyEEfog"
GEMINI_MODEL = "gemini-1.5-flash"
TIMEOUT      = 10


def _encode_image(img: Image.Image) -> str:
    """Realiza a conversão da imagem"""
    if img.mode == "RGBA":
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode()

def _get_model(api_key: str):
    return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=api_key)

"""O comando é para além da tabela, exibir dicas ou comentários sobre o alimento em questão."""
SYSTEM_MSG = (
    "Você é um nutricionista que **OBRIGATORIAMENTE** devolve resposta no "
    "formato especificado. Nunca acrescente texto entre as tags <JSON> e </JSON>."
)

USER_PROMPT = """
Analise a imagem e responda **exatamente** assim:

<JSON>
{"foods":[{"name":"...", "quantity":"..."}]}
</JSON>

Após </JSON>, escreva 1 parágrafo em português comentando o prato
e sua qualidade nutricional. Use nomes de alimentos em português.
"""

_JSON_RE = re.compile(r"<JSON>(.*?)</JSON>", re.DOTALL)

def _extract_json_and_comment(text: str) -> tuple[str, str]:
    m = _JSON_RE.search(text)
    if not m:
        return "", ""
    json_block = m.group(1).strip()

    if json_block.startswith("```json"):
        json_block = json_block[len("```json"):].strip()
    if json_block.endswith("```"):
        json_block = json_block[:-3].strip()

    comment = text.split("</JSON>", 1)[1].strip()
    return json_block, comment

def identificar_comida(img: Image.Image, gemini_api_key: str):
    model   = _get_model(gemini_api_key)
    enc_img = _encode_image(img)

    resp = model.invoke([
        {"role": "system", "content": SYSTEM_MSG},
        {"role": "user",
         "content": [
             {"type": "text",      "text": USER_PROMPT},
             {"type": "image_url", "image_url": f"data:image/jpeg;base64,{enc_img}"},
         ]}
    ])

    raw = resp.content or ""
    json_txt, comment = _extract_json_and_comment(raw)

    try:
        foods = json.loads(json_txt)["foods"]
    except Exception:
        foods = []

    return foods, comment


def _calories_per_100g(food: str) -> float | None:
    """Consulta e retorna os dados com base em calorias a cada 100g do alimento identificado"""
    r = requests.get(
        "https://api.nal.usda.gov/fdc/v1/foods/search",
        params={"query": food, "pageSize": 1, "api_key": FDC_KEY},
        timeout=TIMEOUT
    ).json()

    for hit in r.get("foods", []):
        for n in hit.get("foodNutrients", []):
            if n["nutrientName"] == "Energy":
                return n["value"]          # kcal
    return None

def criar_tabela(foods: list[dict]) -> pd.DataFrame:
    rows = []
    for item in foods:
        kcal = _calories_per_100g(item["name"])
        rows.append({
            "Alimento": item["name"].title(),
            "Porção":   item["quantity"],
            "kcal / 100 g": kcal if kcal is not None else "–"
        })
    return pd.DataFrame(rows)

def total_kcal(foods: list[dict]) -> float:
    return sum(
        _calories_per_100g(item["name"]) or 0
        for item in foods
    )
