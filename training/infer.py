from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch

MODEL_PATH = "models/t5-nl2sql"

tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH)
model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH)
model.eval()


def generate_sql(question, schema, max_length=256):
    input_text = (
        "translate English to SQL:\n"
        f"Question: {question}\n"
        f"Schema:\n{schema}"
    )

    inputs = tokenizer(
        input_text,
        return_tensors="pt",
        truncation=True,
        padding=True
    )

    with torch.no_grad():
        
        outputs = model.generate(
        **inputs,
        max_length=max_length,
        num_beams=5,            # better search
        early_stopping=True,
        no_repeat_ngram_size=3, # avoids trivial outputs
        )


    sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return sql


if __name__ == "__main__":
    # quick manual test
    schema = """
    employee(emp_id, name, salary, department)


    """

    question = "How many employees earn less than 50000?"

    print(generate_sql(question, schema))
