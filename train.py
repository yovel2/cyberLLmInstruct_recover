import os
import time
import torch
import gc
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset

# ==========================================
# CONFIGURATION & PARAMETERS (As per Report)
# ==========================================
MODEL_NAME = "unsloth/Meta-Llama-3.1-8B-Instruct"  # Base model specified in report
MAX_SEQ_LENGTH = 2048  # Specified in report
DATASET_PATH = "data/train_split.jsonl"
OUTPUT_DIR = "outputs/llama-3.1-8b-cyber-finetuned"

# LoRA Parameters (As per report)
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05

# Intermittent Training Constants
TRAIN_SESSION_HOURS = 1.5
SESSION_DURATION_SECS = TRAIN_SESSION_HOURS * 3600
MAX_CHECKPOINTS = 3


def clear_memory():
    """Flushes RAM and VRAM to prevent OOM on Iris Xe."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    print("[*] Memory cleared.")


def load_and_prep_model():
    """Loads model with Unsloth optimization and applies LoRA configuration."""
    print(f"[*] Loading model {MODEL_NAME} using Unsloth (4-bit)...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,  # Auto detection
        load_in_4bit=True,  # Crucial for limited VRAM
    )

    print("[*] Applying QLoRA configuration...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj", ],
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )
    return model, tokenizer


def get_training_args():
    """Returns training arguments specified in the report."""
    return TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,  # Effective batch size = 16 (2 * 8)
        learning_rate=2e-4,
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        optim="paged_adamw_8bit",  # Optimizer specified in report

        # Checkpointing logic
        save_strategy="steps",
        save_steps=100,
        save_total_limit=MAX_CHECKPOINTS,  # Enforcing max 3 checkpoints

        # Stop execution logic (handled via callback/time monitoring usually, simplified here)
        max_steps=2000,  # Example placeholder
        logging_steps=10,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
    )


def train_intermittent_session():
    """Executes a single intermittent training chunk."""
    clear_memory()

    model, tokenizer = load_and_prep_model()

    # Check if continuing from a checkpoint
    checkpoints = [d for d in os.listdir(OUTPUT_DIR) if d.startswith("checkpoint")] if os.path.exists(
        OUTPUT_DIR) else []
    resume_from_checkpoint = os.path.join(OUTPUT_DIR,
                                          max(checkpoints, key=lambda x: int(x.split("-")[1]))) if checkpoints else None

    # Load dataset
    print(f"[*] Loading dataset from {DATASET_PATH}...")
    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",  # Assumes preprocessing combined instruction/output
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_num_proc=2,
        args=get_training_args(),
    )

    print(f"[*] Starting {TRAIN_SESSION_HOURS} hour training chunk...")
    start_time = time.time()

    # In a real rigorous setup, a custom Callback would halt the trainer gracefully
    # after SESSION_DURATION_SECS. For this demonstration code, we simulate the run.
    try:
        trainer.train(resume_from_checkpoint=resume_from_checkpoint)
    except KeyboardInterrupt:
        print("\n[*] Training interrupted (expected for chunking). Saving state...")
        trainer.save_model(os.path.join(OUTPUT_DIR, "manual_chunk_save"))

    elapsed_time = time.time() - start_time
    print(f"[*] Session finished. Elapsed time: {elapsed_time / 3600:.2f} hours.")
    clear_memory()


if __name__ == "__main__":
    train_intermittent_session()