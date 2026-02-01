# services/analysis/plan_model.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class PlanModel:
    def __init__(self, model_path: str):
        self.model_path = model_path
        print("🧠 Loading Model in 4-bit...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

        self.model = AutoModelForCausalLM.from_pretrained(
    model_path,
    device_map={"": "cpu"},
    dtype=torch.float32
)


        self.model.eval()
        print("✅ AI CAD Engine Ready.")

# Example usage:
# model = PlanModel("services/analysis/models/my_model")
# print(model.generate_plan("Create a 3D floor plan for a 2-bedroom apartment"))
