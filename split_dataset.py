import json
import random
import os

# Original dataset from CyberLLMInstruct repo
INPUT_FILE = "data/raw_cyberllminstruct.jsonl"
TRAIN_OUTPUT = "data/train_split.jsonl"
TEST_OUTPUT = "data/test_split.jsonl"


def process_and_split_data():
    """
    Cleans, formats, and splits the data into 90% train and 10% test
    as documented in the final report.
    """
    if not os.path.exists(INPUT_FILE):
        print(f"[-] Input file not found: {INPUT_FILE}")
        return

    processed_data = []

    print("[*] Reading and formatting raw data...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line)
                # Ensure the consistent instruction/output format
                if "instruction" in record and "output" in record:
                    # Combine into a single text block for SFTTrainer
                    formatted_text = f"User: {record['instruction']}\nAssistant: {record['output']}"
                    processed_data.append({"text": formatted_text})
            except json.JSONDecodeError:
                continue

    total_records = len(processed_data)
    print(f"[*] Successfully processed {total_records} records.")

    # Shuffle for random distribution
    random.seed(42)
    random.shuffle(processed_data)

    # 90% Train / 10% Test split
    split_index = int(total_records * 0.90)
    train_data = processed_data[:split_index]
    test_data = processed_data[split_index:]

    print(f"[*] Splitting data: {len(train_data)} Train (90%) | {len(test_data)} Test (10%)")

    # Save to files
    with open(TRAIN_OUTPUT, 'w', encoding='utf-8') as f:
        for item in train_data:
            f.write(json.dumps(item) + '\n')

    with open(TEST_OUTPUT, 'w', encoding='utf-8') as f:
        for item in test_data:
            f.write(json.dumps(item) + '\n')

    print("[+] Splitting complete.")


if __name__ == "__main__":
    process_and_split_data()