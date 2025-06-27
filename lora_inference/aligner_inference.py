from openai import OpenAI
import json
import os
from tqdm import tqdm
import ray
from ray.util.actor_pool import ActorPool
import argparse
ALIGNER_PORT=8011
ALIGNER_API_KEY="lora_aligner"
ALIGNER_MODEL = "/aifs4su/yaodong/models/google/gemma-3-1b-it"

# TEMPLATE = """Editing the following Question-Answer pair to make it more helpful and harmless. ##Question: {prompt} ##Answer: {response} ##Correction:"""
TEMPLATE = """##Question: {prompt} ##Answer: {response} ##Correction:"""

def init_engine():
    return OpenAI(
        base_url=f"http://localhost:{ALIGNER_PORT}/v1",
        api_key=ALIGNER_API_KEY,
    )

@ray.remote
class AlignerActor:
    def __init__(self):
        self.aligner_client = init_engine()

    def inference(self, prompt: str):
        completion = self.aligner_client.chat.completions.create(
            model=ALIGNER_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ]
        )
        return completion.choices[0].message.content

def prepare_test_data(test_file: str):
    raw_data = []
    with open(test_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    # prompt, response
    test_data = []
    for item in tqdm(raw_data, desc="Preparing test data"):
        prompt = item["prompt"]
        response = item["response"]
        aligner_input = TEMPLATE.format(prompt=prompt, response=response)
        test_data.append({
            "prompt": aligner_input,
            "raw_data": {
                "raw_prompt": prompt,
                "original_answer": response,
            },
        })
    return test_data

def main(test_file: str, output_file: str, num_parallel_requests: int = 16):
    test_data = prepare_test_data(test_file)
    actors = [AlignerActor.remote() for _ in range(num_parallel_requests)]
    pool = ActorPool(actors)
    
    prompts = [item['prompt'] for item in test_data]
    
    results_generator = pool.map(
        lambda actor, prompt: actor.inference.remote(prompt),
        prompts
    )
    
    for i, response in enumerate(tqdm(results_generator, total=len(prompts), desc="Inferring Aligner")):
        test_data[i]["correction"] = response

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Aligner Inference Script')
    parser.add_argument('--aligner_name', type=str, required=True, help='Name of the aligner model')
    parser.add_argument('--file_path', type=str, required=True, help='Output directory path')
    parser.add_argument('--test_file_list', type=str, nargs='+', required=True, help='List of test files to process')
    parser.add_argument('--num_parallel_requests', type=int, default=16, help='Number of parallel requests')
    
    args = parser.parse_args()
    
    ray.init()
    aligner_name = args.aligner_name
    file_path = args.file_path
    test_file_list = args.test_file_list
    
    for test_file in test_file_list:
        path_parts = test_file.split('/')
        output_file = os.path.join(file_path, path_parts[-3], path_parts[-2], aligner_name, f"test_data_aligned.json")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        main(test_file=test_file, output_file=output_file, num_parallel_requests=args.num_parallel_requests)
    ray.shutdown()
