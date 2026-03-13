import json
import os
import re


def read_schema(schema_path):
    '''
    Read the .schema file and return CREATE TABLE DDL for all tables.
    '''
    with open(schema_path) as f:
        schema = json.load(f)

    ents = schema.get("ents", schema)
    ddl_statements = []

    for table_name, columns in ents.items():
        col_defs = []
        for col_name, col_info in columns.items():
            col_type = col_info.get("type", "TEXT")
            col_defs.append(f"  {col_name} {col_type}")
        cols_str = ",\n".join(col_defs)
        ddl = f"CREATE TABLE {table_name} (\n{cols_str}\n);"
        ddl_statements.append(ddl)

    return "\n\n".join(ddl_statements)


def extract_sql_query(response):
    '''
    Extract the SQL query from the model's response using multi-pattern
    regex extraction with priority ordering.
    '''
    # Strip special tokens
    text = response
    for token in ["<end_of_turn>", "<eos>", "<bos>"]:
        text = text.replace(token, "")

    # Strip echoed prompt: find last <start_of_turn>model marker
    marker = "<start_of_turn>model"
    idx = text.rfind(marker)
    if idx != -1:
        text = text[idx + len(marker):]

    text = text.strip()

    # Priority 1: ```sql ... ``` code blocks
    match = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
        return sql.replace('\n', ' ').strip()

    # Priority 2: generic ``` ... ``` code blocks
    match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if match:
        sql = match.group(1).strip()
        return sql.replace('\n', ' ').strip()

    # Priority 3: SELECT ... ; pattern
    match = re.search(r"(SELECT\s+.*?;)", text, re.DOTALL | re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
        return sql.replace('\n', ' ').strip()

    # Priority 4: First line starting with SELECT
    for line in text.split('\n'):
        if line.strip().upper().startswith('SELECT'):
            return line.strip()

    # Priority 5: Fallback -- return stripped text as-is
    return text.replace('\n', ' ').strip()


def save_logs(output_path, sql_em, record_em, record_f1, error_msgs):
    '''
    Save the logs of the experiment to files.
    You can change the format as needed.
    '''
    with open(output_path, "w") as f:
        f.write(f"SQL EM: {sql_em}\nRecord EM: {record_em}\nRecord F1: {record_f1}\nModel Error Messages: {error_msgs}\n")
