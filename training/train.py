import random
from pathlib import Path

import torch
from torch.utils.data import Dataset

from transformers import (
    T5Tokenizer,
    T5ForConditionalGeneration,
    Trainer,
    TrainingArguments
)

from preprocess import load_spider, build_t5_example


# ---------------- CONFIG ----------------
MODEL_NAME = "t5-small"
OUTPUT_DIR = "models/t5-nl2sql"
MAX_SAMPLES = 2000      # keep CPU-safe
MAX_INPUT_LEN = 512
MAX_TARGET_LEN = 256
EPOCHS = 2
BATCH_SIZE = 2
# ----------------------------------------


class SpiderDataset(Dataset):
    def __init__(self, data, tables, tokenizer):
        self.samples = data
        self.tables = tables
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        input_text, target_text = build_t5_example(
            self.samples[idx], self.tables
        )

        model_inputs = self.tokenizer(
            input_text,
            truncation=True,
            padding="max_length",
            max_length=MAX_INPUT_LEN,
            return_tensors="pt"
        )

        labels = self.tokenizer(
            target_text,
            truncation=True,
            padding="max_length",
            max_length=MAX_TARGET_LEN,
            return_tensors="pt"
        )

        return {
            "input_ids": model_inputs["input_ids"].squeeze(),
            "attention_mask": model_inputs["attention_mask"].squeeze(),
            "labels": labels["input_ids"].squeeze()
        }


def main():
    print("Loading Spider data...")
    train_data, tables = load_spider()

    random.shuffle(train_data)
    train_data = train_data[:MAX_SAMPLES]

    print(f"Using {len(train_data)} training samples")

    tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
    model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)

    dataset = SpiderDataset(train_data, tables, tokenizer)

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=4,
        learning_rate=3e-4,
        logging_steps=50,
        save_strategy="epoch",
        save_total_limit=1,
        fp16=False,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset
    )

    print("Starting training...")
    trainer.train()

    print("Saving model...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print("Training complete.")


if __name__ == "__main__":
    main()
