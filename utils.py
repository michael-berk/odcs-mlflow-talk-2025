import base64
import os
import json
import random

from PIL import Image
from io import BytesIO

DATA_DIRECTORY = "./data"
ANNOTATIONS_DIRECTORY = os.path.join(DATA_DIRECTORY, "annotations")
IMAGES_DIRECTORY = os.path.join(DATA_DIRECTORY, "images")

def _set_openai_api_key_for_demo() -> bool:
    """Dummy method for doing easy auth in a notebook environment during the live demo."""
    try:
        with open("/Users/michael.berk/Desktop/openai_api_key.txt", "r") as f:
            os.environ["OPENAI_API_KEY"] = f.read().strip()
            return True
    except Exception:
        pass 
    
    return False

def _compress_image(file_path: str, quality: int = 40, max_size: tuple[int, int] = (1000, 1000)) -> bytes:
    """Compresses an image by resizing and converting to JPEG with given quality."""
    with Image.open(file_path) as img:
        img = img.convert("RGB")  # Ensure JPEG compatibility
        img.thumbnail(max_size)  # Resize
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()


def get_image(
    file_name: str, directory: str = IMAGES_DIRECTORY, encode_as_str: bool = False
) -> bytes:
    file_name += ".png" if not file_name.endswith(".png") else file_name
    path = os.path.join(directory, file_name)
    with open(path, "rb") as f:
        file = f.read()
        compressed = _compress_image(path)

        if encode_as_str:
            return base64.b64encode(compressed).decode("utf-8")
        else:
            return compressed 


def _extract_qa_pairs(data: dict) -> dict:
    """Extracts question-answer pairs from OCR-style linked data."""
    qa_pairs = {}

    elements = {item["id"]: item for item in data}
    for item in data:
        if item["label"] != "question" or not item["linking"]:
            continue
        for q_id, a_id in item["linking"]:
            if q_id != item["id"]:
                continue
            answer = elements.get(a_id)
            if answer and answer["label"] == "answer":
                q_text = " ".join(w["text"] for w in item["words"])
                a_text = " ".join(w["text"] for w in answer["words"])
                qa_pairs[q_text] = a_text
    return qa_pairs

def get_json(file_name: str, directory: str = ANNOTATIONS_DIRECTORY) -> dict:
    file_name += ".json" if not file_name.endswith(".json") else file_name
    path = os.path.join(directory, file_name)
    with open(path, "r", encoding="utf-8") as f:
        contents = json.load(f)["form"]
        if isinstance(contents, list):
            if all(isinstance(page, list) for page in contents):
                flat_items = [item for page in contents for item in page]
            else:
                flat_items = contents
            return _extract_qa_pairs(flat_items)
        else:
            return _extract_qa_pairs(contents)


def get_random_files(
    directory: str = ANNOTATIONS_DIRECTORY, n: int = 1
) -> list[str] | str | None:
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory {directory} does not exist.")

    if files := os.listdir(directory):
        selected_filed = random.sample(files, k=n)
        cleaned_files = [file.rsplit(".", 1)[0] for file in selected_filed]

        if len(cleaned_files) == 1:
            return cleaned_files[0]

        return cleaned_files

    return None
