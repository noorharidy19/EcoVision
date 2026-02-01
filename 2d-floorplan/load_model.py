from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
from transformers import BitsAndBytesConfig

BASE_MODEL = "codellama/CodeLlama-7b-Instruct-hf"
LORA_PATH = "C:\\Users\\lenovo\\Desktop\\grad project\\final model\\floorplan_model_v1"  # or final adapter


bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

print("🧠 Loading Model in 4-bit...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,
    quantization_config=bnb_config,
    device_map="auto"
)

model = PeftModel.from_pretrained(model, LORA_PATH)
model.eval()
print("✅ AI CAD Engine Ready.")