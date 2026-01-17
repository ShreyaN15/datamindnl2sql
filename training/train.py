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


# ================= CONFIG =================

MODEL_NAME = "t5-base"

BASE_DIR = Path(".")
OUTPUT_DIR = BASE_DIR / "checkpoints"

MAX_INPUT_LEN = 512
MAX_TARGET_LEN = 256

EPOCHS = 20
PER_DEVICE_BATCH = 8          # A40 can handle this easily
GRAD_ACC_STEPS = 2            # effective batch = 16
LEARNING_RATE = 3e-5

WARMUP_STEPS = 500
WEIGHT_DECAY = 0.01

# =========================================


class SpiderDataset(Dataset):
    def __init__(self, samples, tables, tokenizer):
        self.samples = samples
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
            max_length=MAX_INPUT_LEN,
            truncation=True,
            padding="max_length"
        )

        labels = self.tokenizer(
            target_text,
            max_length=MAX_TARGET_LEN,
            truncation=True,
            padding="max_length"
        )

        model_inputs["labels"] = labels["input_ids"]

        return {k: torch.tensor(v) for k, v in model_inputs.items()}


def main():
    print("Loading Spider dataset...")
    train_data, dev_data, tables = load_spider()

    print(f"Train samples: {len(train_data)}")
    print(f"Dev samples:   {len(dev_data)}")

    tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
    model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)

    train_dataset = SpiderDataset(train_data, tables, tokenizer)
    dev_dataset = SpiderDataset(dev_data, tables, tokenizer)

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        overwrite_output_dir=True,

        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,

        per_device_train_batch_size=PER_DEVICE_BATCH,
        per_device_eval_batch_size=PER_DEVICE_BATCH,
        gradient_accumulation_steps=GRAD_ACC_STEPS,

        warmup_steps=WARMUP_STEPS,
        weight_decay=WEIGHT_DECAY,

        fp16=True,

        evaluation_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,

        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",

        logging_steps=100,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=dev_dataset,
        tokenizer=tokenizer
    )

    print("Starting training...")
    trainer.train()

    print("Saving final model...")
    trainer.save_model(OUTPUT_DIR / "final")
    tokenizer.save_pretrained(OUTPUT_DIR / "final")

    print("Training complete.")


if __name__ == "__main__":
    main()
