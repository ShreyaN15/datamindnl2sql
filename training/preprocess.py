import json
from pathlib import Path

SPIDER_PATH = Path("training/datasets/spider")

def load_spider():
    with open(SPIDER_PATH / "train_spider.json") as f:
        train_data = json.load(f)

    with open(SPIDER_PATH / "tables.json") as f:
        tables = json.load(f)

    return train_data, tables


def format_schema(schema):
    lines = []

    table_names = schema["table_names_original"]
    column_names = schema["column_names_original"]

    for table_id, table_name in enumerate(table_names):
        cols = [
            col_name
            for col_table_id, col_name in column_names
            if col_table_id == table_id
        ]
        lines.append(f"{table_name}({', '.join(cols)})")

    return "\n".join(lines)


def build_t5_example(sample, tables):
    question = sample["question"]
    sql = sample["query"]
    db_id = sample["db_id"]

    # get correct schema for this db
    schema = [t for t in tables if t["db_id"] == db_id][0]
    schema_text = format_schema(schema)

    input_text = (
        "translate English to SQL:\n"
        f"Question: {question}\n"
        f"Schema:\n{schema_text}"
    )

    target_text = sql

    return input_text, target_text

if __name__ == "__main__":
    train_data, tables = load_spider()

    input_text, target_text = build_t5_example(train_data[0], tables)

    print("INPUT (to model):\n")
    print(input_text)
    print("\nTARGET (SQL):\n")
    print(target_text)
