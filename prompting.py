import os, argparse, random
from tqdm import tqdm

import torch
from transformers import GemmaTokenizerFast, GemmaForCausalLM
from transformers import GemmaTokenizer, AutoModelForCausalLM
from transformers import BitsAndBytesConfig

from utils import set_random_seeds, compute_metrics, save_queries_and_records, compute_records
from prompting_utils import read_schema, extract_sql_query, save_logs
from load_data import load_prompting_data
from part3.model import initialize_model_and_tokenizer

from src.config import resolve_device
DEVICE = torch.device(resolve_device())


def get_args():
    '''
    Arguments for prompting. You may choose to change or extend these as you see fit.
    '''
    parser = argparse.ArgumentParser(
        description='Text-to-SQL experiments with prompting.')

    parser.add_argument('-s', '--shot', type=int, default=0,
                        help='Number of examples for k-shot learning (0 for zero-shot)')
    parser.add_argument('-p', '--ptype', type=int, default=0,
                        help='Prompt type')
    parser.add_argument('-m', '--model', type=str, default='gemma',
                        help='Model to use for prompting: gemma (gemma-1.1-2b-it) or codegemma (codegemma-7b-it)')
    parser.add_argument('-q', '--quantization', action='store_true',
                        help='Use a quantized version of the model (e.g. 4bits)')

    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed to help reproducibility')
    parser.add_argument('--experiment_name', type=str, default='experiment',
                        help="How should we name this experiment?")
    parser.add_argument('--example_selection', type=str, default='random',
                        choices=['random', 'bm25'],
                        help='Example selection strategy for k-shot')
    parser.add_argument('--include_schema', type=lambda x: x.lower() != 'false',
                        default=True,
                        help='Include database schema in prompt (default: True)')
    parser.add_argument('--include_instructions', type=lambda x: x.lower() != 'false',
                        default=True,
                        help='Include instructions in prompt (default: True)')
    parser.add_argument('--eval_splits', type=str, nargs='+', default=["dev", "test"],
                        choices=["dev", "test"],
                        help='Which splits to evaluate (default: dev test)')

    args = parser.parse_args()
    return args


def create_prompt(sentence, k, schema_text="", examples=None, include_instructions=True, include_schema=True):
    '''
    Function for creating a prompt for zero or few-shot prompting.

    Inputs:
        * sentence (str): A text string
        * k (int): Number of examples in k-shot prompting
        * schema_text (str): Database schema DDL text
        * examples (list): List of (nl, sql) tuples for k-shot examples
        * include_instructions (bool): Whether to include task instructions
        * include_schema (bool): Whether to include schema in prompt
    '''
    parts = []

    # Schema
    if include_schema and schema_text:
        parts.append("Database schema:\n" + schema_text)

    # Instructions
    if include_instructions:
        parts.append("Translate the following question into SQL. Output only the SQL query.")

    # K-shot examples
    if examples and k > 0:
        for nl, sql in examples[:k]:
            parts.append(f"Question: {nl}\nSQL: {sql}")

    # Target question
    parts.append(f"Question: {sentence}\nSQL:")

    user_content = "\n\n".join(parts)
    prompt = f"<start_of_turn>user\n{user_content}<end_of_turn>\n<start_of_turn>model\n"
    return prompt


def exp_kshot(tokenizer, model, inputs, k, schema_text="", examples=None,
              include_instructions=True, include_schema=True,
              bm25_index=None, example_selection="random",
              train_x=None, train_y=None, max_new_tokens=128):
    '''
    k-shot prompting experiments using the provided model and tokenizer.
    This function generates SQL queries from text prompts and evaluates their accuracy.

    Inputs:
        * tokenizer
        * model
        * inputs (List[str]): A list of text strings
        * k (int): Number of examples in k-shot prompting
        * schema_text (str): Database schema DDL
        * examples (list): Fixed list of (nl, sql) examples for random selection
        * include_instructions (bool): Whether to include instructions
        * include_schema (bool): Whether to include schema
        * bm25_index: BM25 index for per-query example selection
        * example_selection (str): "random" or "bm25"
        * train_x, train_y: Training data needed for BM25 selection
        * max_new_tokens (int): Maximum tokens to generate (default 128)
    '''
    raw_outputs = []
    extracted_queries = []

    # Determine device for input_ids
    if hasattr(model, 'device'):
        target_device = model.device
    else:
        target_device = DEVICE

    # Build stop token list: EOS + end-of-turn token (107 for Gemma)
    eos_token_id = tokenizer.eos_token_id
    eot_token_id = 107  # <end_of_turn> token for Gemma models

    for i, sentence in tqdm(enumerate(inputs)):
        # Per-query BM25 example selection
        if example_selection == "bm25" and bm25_index is not None and k > 0:
            from part3.data import select_examples_bm25
            query_examples = select_examples_bm25(sentence, train_x, train_y, bm25_index, k)
        else:
            query_examples = examples

        prompt = create_prompt(sentence, k, schema_text, query_examples,
                               include_instructions, include_schema)

        input_ids = tokenizer(prompt, return_tensors="pt").to(target_device)
        outputs = model.generate(
            **input_ids,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            eos_token_id=[eos_token_id, eot_token_id],
        )
        response = tokenizer.decode(outputs[0])
        raw_outputs.append(response)

        # Extract the SQL query
        extracted_query = extract_sql_query(response)
        extracted_queries.append(extracted_query)
    return raw_outputs, extracted_queries


def eval_outputs(extracted_queries, gt_sql_path, model_sql_path, gt_record_path, model_record_path):
    '''
    Evaluate the outputs of the model by computing the metrics.

    Inputs:
        * extracted_queries (List[str]): Extracted SQL queries from model output
        * gt_sql_path (str): Path to ground-truth SQL file
        * model_sql_path (str): Path to save model SQL predictions
        * gt_record_path (str): Path to ground-truth records pickle
        * model_record_path (str): Path to save model records pickle
    '''
    # Save model predictions first
    save_queries_and_records(extracted_queries, model_sql_path, model_record_path)

    # Compute metrics
    sql_em, record_em, record_f1, model_error_msgs = compute_metrics(
        gt_sql_path, model_sql_path, gt_record_path, model_record_path
    )

    # Compute error rate
    error_rate = sum(1 for msg in model_error_msgs if msg) / len(model_error_msgs)

    return sql_em, record_em, record_f1, model_error_msgs, error_rate


def main():
    '''
    Note: this code serves as a basic template for the prompting task. You can but
    are not required to use this pipeline.
    You can design your own pipeline, and you can also modify the code below.
    '''
    args = get_args()
    shot = args.shot
    ptype = args.ptype
    model_name = args.model
    to_quantize = args.quantization
    experiment_name = args.experiment_name

    set_random_seeds(args.seed)

    data_folder = 'data'
    train_x, train_y, dev_x, dev_y, test_x = load_prompting_data(data_folder)

    # Read database schema
    schema_text = read_schema("data/flight_database.schema")

    # Sample k-shot examples from training set
    examples = None
    bm25_index = None
    if shot > 0:
        if args.example_selection == "bm25":
            from part3.data import build_bm25_index
            bm25_index = build_bm25_index(train_x)
        else:
            examples = random.sample(list(zip(train_x, train_y)), shot)

    # Model and tokenizer
    tokenizer, model = initialize_model_and_tokenizer(model_name, to_quantize)

    for eval_split in args.eval_splits:
        eval_x, eval_y = (dev_x, dev_y) if eval_split == "dev" else (test_x, None)

        raw_outputs, extracted_queries = exp_kshot(
            tokenizer, model, eval_x, shot,
            schema_text=schema_text,
            examples=examples,
            include_instructions=args.include_instructions,
            include_schema=args.include_schema,
            bm25_index=bm25_index,
            example_selection=args.example_selection,
            train_x=train_x,
            train_y=train_y,
        )

        gt_sql_path = os.path.join(f'data/{eval_split}.sql')
        gt_record_path = os.path.join(f'records/ground_truth_{eval_split}.pkl')
        model_sql_path = os.path.join(f'results/llm_{experiment_name}_{eval_split}.sql')
        model_record_path = os.path.join(f'records/llm_{experiment_name}_{eval_split}.pkl')

        if eval_y is not None:
            sql_em, record_em, record_f1, model_error_msgs, error_rate = eval_outputs(
                extracted_queries,
                gt_sql_path, model_sql_path,
                gt_record_path, model_record_path
            )
            print(f"{eval_split} set results: ")
            print(f"Record F1: {record_f1}, Record EM: {record_em}, SQL EM: {sql_em}")
            print(f"{eval_split} set results: {error_rate*100:.2f}% of the generated outputs led to SQL errors")

            # Save logs
            log_path = f"results/llm_{experiment_name}_{eval_split}_log.txt"
            save_logs(log_path, sql_em, record_em, record_f1, model_error_msgs)
        else:
            # Test split -- save predictions only (no ground truth)
            save_queries_and_records(extracted_queries, model_sql_path, model_record_path)
            print(f"Test predictions saved to {model_sql_path}")


if __name__ == "__main__":
    from src.utils.gpu_lock import GpuLock
    with GpuLock():
        main()
