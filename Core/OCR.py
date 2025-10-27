# pip install -U transformers
# pip install  TensorFlow 
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
# pip install -U jupyter ipywidgets
# pip install accelerate
# pip install einops timm
# pip install flash-attn --no-build-isolation
# pip install pillow
import io
import re
import torch
import torchvision.transforms as T
from PIL import Image
from torchvision.transforms.functional import InterpolationMode
from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM
import json
from PyPDF2 import PdfReader
from io import BytesIO
from fastapi import UploadFile

# ===============================
# IMAGE PREPROCESSING
# ===============================
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

def build_transform(input_size):
    return T.Compose([
        T.Lambda(lambda img: img.convert('RGB') if img.mode != 'RGB' else img),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])

def find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    best_ratio_diff, best_ratio = float('inf'), (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff, best_ratio = ratio_diff, ratio
        elif ratio_diff == best_ratio_diff and area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
            best_ratio = ratio
    return best_ratio

def dynamic_preprocess(image, min_num=1, max_num=12, image_size=448, use_thumbnail=False):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height
    target_ratios = sorted(
        {(i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1)
         if min_num <= i * j <= max_num},
        key=lambda x: x[0] * x[1]
    )
    target_aspect_ratio = find_closest_aspect_ratio(aspect_ratio, target_ratios, orig_width, orig_height, image_size)
    target_width, target_height = image_size * target_aspect_ratio[0], image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    resized_img = image.resize((target_width, target_height))
    processed_images = [
        resized_img.crop((
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size
        ))
        for i in range(blocks)
    ]
    if use_thumbnail and len(processed_images) != 1:
        processed_images.append(image.resize((image_size, image_size)))
    return processed_images

def load_image(image_file, input_size=448, max_num=12):
    image = Image.open(image_file).convert('RGB')
    transform = build_transform(input_size)
    images = dynamic_preprocess(image, image_size=input_size, use_thumbnail=True, max_num=max_num)
    return torch.stack([transform(img) for img in images])

# ===============================
# MODEL 1: VINTERN
# ===============================

vintern_model = None
vintern_tokenizer = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ======================
# 2️⃣ Hàm load model — chỉ gọi 1 lần ở startup
# ======================
def load_vintern_model():
    """
    Load mô hình Vintern lên GPU hoặc CPU tùy tài nguyên.
    Gọi một lần khi khởi động server.
    """
    global vintern_model, vintern_tokenizer, device

    if vintern_model is not None:
        print("✅ Vintern model already loaded.")
        return vintern_model, vintern_tokenizer

    model_name = "5CD-AI/Vintern-1B-v3_5"
    print(f"🔹 Loading model {model_name}...")

    try:
        vintern_model = AutoModel.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
            use_flash_attn=False,
        ).eval().to(device)
    except RuntimeError as e:
        # fallback sang CPU nếu GPU hết RAM
        print("⚠️ GPU memory error, switching to CPU.")
        torch.cuda.empty_cache()
        vintern_model = AutoModel.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
            use_flash_attn=False,
        ).eval().to("cpu")
        device = torch.device("cpu")

    vintern_tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_fast=False,
    )

    print(f"✅ Vintern model loaded successfully on {device}.")
    return vintern_model, vintern_tokenizer

def run_vintern(image_path):
    if vintern_model is None or vintern_tokenizer is None:
        raise RuntimeError("❌ Model chưa được load. Gọi load_vintern_model() trước!")

    pixel_values = load_image(image_path, max_num=6).to(torch.bfloat16).cuda()
    generation_config = dict(max_new_tokens=2000, do_sample=False, num_beams=3, repetition_penalty=2.5)

    question = """
    Extract skills, work experience, education, projects, certifications, awards, and other professional details from this CV image. 
    Exclude all personal information. 
    Return the result in Markdown format. 
    Respond in English only.
    """
    response, _ = vintern_model.chat(vintern_tokenizer, pixel_values, question, generation_config, history=None, return_history=True)
    return response  # Đây chính là CR

# ===============================
# MODEL 2: QWEN
# ===============================
def run_qwen(JD, CR):
    model_id = "Gensyn/Qwen2.5-1.5B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    prompt = f"""You are a recruitment assistant. Your task is to evaluate a candidate’s CV against the job description.

List each job requirement separately and respond with:

'Met' — if the candidate meets the requirement
'Not Met' — if the candidate does not meet it or the information is unclear

Do not explain. Do not add comments. Only return a JSON object with each requirement and its corresponding status.

### Job Description (JD):
{JD}

### Candidate Resume (CR):
{CR}

Return the result in JSON format.
"""

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=1000,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        pad_token_id=tokenizer.eos_token_id
    )
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return generated_text[len(prompt):].strip()

# ===============================
# JSON PROCESSING (NEW)
# ===============================
def parse_evaluation(eval_json: dict):
    result = {"Met": [], "Not_Met": []}

    for key, value in eval_json.items():
        if isinstance(value, str) and value.lower() == "met":
            result["Met"].append(key)
        else:
            result["Not_Met"].append(key)

    # Tính toán thống kê
    met_count = len(result["Met"])
    not_met_count = len(result["Not_Met"])
    total = met_count + not_met_count
    ratio = met_count / total if total > 0 else 0.0

    # Lưu vào dict
    result["Met_Count"] = met_count
    result["Not_Met_Count"] = not_met_count
    result["Total"] = total
    result["Ratio"] = ratio
    result["Ratio_Percent"] = f"{ratio:.2%}"

    return result

def clean_and_parse(result_json: str):
    cleaned = result_json.strip()

    # Gỡ bỏ ký tự đánh dấu code block như ```json ... ```
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    # Loại bỏ comment kiểu // ...
    cleaned = re.sub(r'//.*', '', cleaned)

    # Loại bỏ comment kiểu # ...
    cleaned = re.sub(r'#.*', '', cleaned)

    # Loại bỏ dấu phẩy thừa trước dấu đóng ngoặc } hoặc ]
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)

    # Xử lý ký tự đặc biệt không hợp lệ (nếu có)
    cleaned = cleaned.replace("\u2013", "-").replace("\u2014", "-")

    # 🧩 Tìm phần JSON lớn nhất (toàn bộ, không bị cắt)
    # Dấu `*` thay vì `*?` để match dài nhất có thể (greedy)
    json_match = re.search(r'\{[\s\S]*\}', cleaned)
    if json_match:
        cleaned = json_match.group(0)
    else:
        print("❌ Không tìm thấy JSON hợp lệ trong chuỗi!")
        print("Raw output:\n", result_json)
        raise ValueError("No valid JSON found")

    # 🧠 Parse JSON
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("❌ JSON parse error:", e)
        print("Raw output:\n", result_json)
        print("\n--- Cleaned Attempt ---\n", cleaned)
        raise ValueError("Invalid JSON format from model")

    # ✅ Gọi hàm xử lý sau khi parse thành công
    return parse_evaluation(data)

def compare_OCR(image, JD):
    CR = run_vintern(image)
    qwen_output = run_qwen(JD, CR)
    result = clean_and_parse(qwen_output)
    for r in result["Met"]:
        print(f"- {r}")
    for r in result["Not_Met"]:
        print(f"- {r}")
    return result

async def scan_pdf(file: UploadFile):
    contents = await file.read()
    reader = PdfReader(io.BytesIO(contents))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# So sánh CV và JD chỉ với Qwen (không qua Vintern)
def compare_qwen(JD, CR):
    qwen_output = run_qwen(JD, CR)
    result = clean_and_parse(qwen_output)
    return result

# So sánh CV và JD
def compare(url, JD, file_type):
    if file_type == "pdf":
        CR = scan_pdf(url)
    elif file_type == "image":
        CR = run_vintern(url)
    qwen_output = run_qwen(JD, CR)
    result = clean_and_parse(qwen_output)
    return result