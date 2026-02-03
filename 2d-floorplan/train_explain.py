# import os
# import json
# import torch
# import re
# from torch.utils.data import IterableDataset
# from transformers import AutoTokenizer

# class FloorplanExplanationPairedDataset(IterableDataset):
#     def __init__(self, floorplan_folder, explain_folder, tokenizer_name="codellama/CodeLlama-7b-Instruct-hf", max_length=1024, mode="train"):
#         self.floorplan_folder = floorplan_folder
#         self.explain_folder = explain_folder
#         self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, padding_side="right")
#         self.max_length = max_length

#         if self.tokenizer.pad_token is None:
#             self.tokenizer.pad_token = self.tokenizer.eos_token

       
#         fp_files = {f.split('_')[1].split('.')[0]: os.path.join(floorplan_folder, f)
#                     for f in os.listdir(floorplan_folder) if f.endswith(".json")}

        
#         exp_files = {f.split('_')[1].split('.')[0]: os.path.join(explain_folder, f)
#                      for f in os.listdir(explain_folder) if f.endswith(".json")}

#         common_ids = sorted(list(set(fp_files.keys()) & set(exp_files.keys())))
#         self.paired_files = [(fp_files[idx], exp_files[idx]) for idx in common_ids]

    
#         split_idx = int(len(self.paired_files) * 0.98)
#         self.files = self.paired_files[:split_idx] if mode == "train" else self.paired_files[split_idx:]

#         print(f" Found {len(self.paired_files)} paired files. Mode: {mode}")

#     def __iter__(self):
#         for fp_path, exp_path in self.files:
         
#             with open(fp_path, "r", encoding='utf-8') as f:
#                 fp_raw = json.load(f)

   
#             with open(exp_path, "r", encoding='utf-8') as f:
#                 exp_data = json.load(f)

#             compact_context = {
#                 "unit_type": fp_raw.get("unitType", "Apartment"),
#                 "total_area": round(fp_raw.get("net_area", 0), 2),
#                 "rooms": [
#                     {
#                         "type": r.get("type"),
#                         "centroid": [round(c, 1) for c in r.get("centroid", [])] if "centroid" in r else None
#                     } for r in fp_raw.get("rooms", []) if r.get("type") != "inner"
#                 ]
#             }
#             context_str = json.dumps(compact_context, separators=(',', ':'))

#             prompt_text = (
#                 f"### System:\nYou are an Architectural AI. Translate the floorplan JSON coordinates into a technical description.\n\n"
#                 f"### Context:\n{context_str}\n\n"
#                 f"### User:\nExplain this floorplan design.\n\n"
#                 f"### Assistant:\n"
#             )

#             target_text = exp_data["explanation"] + self.tokenizer.eos_token

#             # Tokenization & Masking
#             prompt_ids = self.tokenizer.encode(prompt_text, add_special_tokens=False)
#             target_ids = self.tokenizer.encode(target_text, add_special_tokens=False)

#             full_ids = (prompt_ids + target_ids)[:self.max_length]
#             labels = ([-100] * len(prompt_ids)) + target_ids
#             labels = labels[:self.max_length]

#             # Padding
#             padding_len = self.max_length - len(full_ids)
#             attention_mask = [1] * len(full_ids) + [0] * padding_len
#             full_ids += [self.tokenizer.pad_token_id] * padding_len
#             labels += [-100] * padding_len

#             yield {
#                 "input_ids": torch.tensor(full_ids, dtype=torch.long),
#                 "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
#                 "labels": torch.tensor(labels, dtype=torch.long)
#             }
# import torch
# from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
# from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
# MODEL_NAME = "codellama/CodeLlama-7b-Instruct-hf"


# bnb_config = BitsAndBytesConfig(
#     load_in_4bit=True,
#     bnb_4bit_quant_type="nf4",
#     bnb_4bit_compute_dtype=torch.float16,
#     bnb_4bit_use_double_quant=True,
# )

# tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
# tokenizer.pad_token = tokenizer.eos_token

# model = AutoModelForCausalLM.from_pretrained(
#     MODEL_NAME,
#     quantization_config=bnb_config,
#     device_map="auto",   
#     trust_remote_code=True
# )
# model.config.use_cache = False


# model.gradient_checkpointing_enable()
# model = prepare_model_for_kbit_training(model)

# from peft import LoraConfig, get_peft_model

# lora_config = LoraConfig(
#     r=16,
#     lora_alpha=32,
#     target_modules=["q_proj", "v_proj"],
#     lora_dropout=0.05,
#     bias="none",
#     task_type="CAUSAL_LM"
# )

# model = get_peft_model(model, lora_config)
# model.print_trainable_parameters()

# from transformers import AutoModelForCausalLM, TrainingArguments, Trainer, BitsAndBytesConfig
# OUTPUT_DIR = "./floorplan_model_v2"
# # ---------------- 4. TRAINING ARGUMENTS ----------------
# training_args = TrainingArguments(
#     output_dir=OUTPUT_DIR,
#     per_device_train_batch_size=4,      
#     gradient_accumulation_steps=2,      
#     learning_rate=2e-4,
#     num_train_epochs=1,
#     warmup_steps=100,
#     max_steps=500,
#     fp16=False,                         
#     bf16=True,
#     optim="adamw_8bit",                 
#     dataloader_num_workers=4,           
#     report_to="tensorboard",            
#     logging_steps=10                    
# )
# trainer = Trainer(
#     model=model,
#     train_dataset=dataset,
#     args=training_args,
# )

# print("Starting training...")
# trainer.train()

