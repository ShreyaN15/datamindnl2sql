import json
from pathlib import Path

# Path to Spider dataset
SPIDER_PATH = Path("spider")


def load_spider():
    with open(SPIDER_PATH / "train_spider.json") as f:
        train_data = json.load(f)

    with open(SPIDER_PATH / "dev.json") as f:
        dev_data = json.load(f)

    with open(SPIDER_PATH / "tables.json") as f:
        tables = json.load(f)

    return train_data, dev_data, tables


def format_schema(schema):
    """
    Strongly grounded schema representation.
    Fully qualify columns with table names and group them clearly.
    """
    lines = []

    table_names = schema["table_names_original"]
    column_names = schema["column_names_original"]

    # Build table -> columns mapping
    table_to_cols = {i: [] for i in range(len(table_names))}
    for col_table_id, col_name in column_names:
        if col_table_id >= 0:  # ignore '*'
            table_to_cols[col_table_id].append(col_name)

    # Format schema
    for table_id, table_name in enumerate(table_names):
        lines.append(f"TABLE {table_name}:")
        for col in table_to_cols[table_id]:
            lines.append(f"- {table_name}.{col}")
        lines.append("")  # blank line between tables

    return "\n".join(lines)




def build_t5_example(sample, tables):
    question = sample["question"]
    sql = sample["query"]
    db_id = sample["db_id"]

    # Find correct schema
    schema = next(t for t in tables if t["db_id"] == db_id)
    schema_text = format_schema(schema)

    input_text = (
        "translate English to SQL:\n"
        f"Question: {question}\n"
        f"Schema:\n{schema_text}"
    )

    target_text = sql

    return input_text, target_text


if __name__ == "__main__":
    train_data, _, tables = load_spider()
    inp, out = build_t5_example(train_data[0], tables)

    print("INPUT:\n")
    print(inp)
    print("\nTARGET:\n")
    print(out)
