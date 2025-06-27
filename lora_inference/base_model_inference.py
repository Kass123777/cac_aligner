from openai import OpenAI
import json
import os
from tqdm import tqdm
import ray
import traceback
import time

BASE_MODEL_PORT=8012
BASE_MODEL_API_KEY="base_model"
BASE_MODEL = "/aifs4su/hansirui_1st/boyuan/llama_sft_70b/slice_2167"
model_name = 'llama_sft_70b_slice_2167'

def init_engine():
    return OpenAI(
        base_url=f"http://localhost:{BASE_MODEL_PORT}/v1",
        api_key=BASE_MODEL_API_KEY,
    )

def format_prompt_for_alpaca(prompt: str, system_message: str = None):
    """
    根据Alpaca模板格式化消息
    """
    messages = []
    
    # 添加系统消息（如果有）
    if system_message:
        messages.append({"role": "system", "content": system_message})
    
    # 添加用户指令
    messages.append({"role": "user", "content": prompt})
    
    return messages

@ray.remote
class InferenceActor:
    def __init__(self):
        self.client = init_engine()

    def inference(self, index: int, prompt: str):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 根据Alpaca模板格式化消息
                # 你可以根据需要添加系统消息或调整提示词
                system_message = "You are a helpful assistant. Please provide detailed and accurate responses."
                
                formatted_messages = format_prompt_for_alpaca(prompt, system_message)
                
                completion = self.client.chat.completions.create(
                    model=BASE_MODEL,
                    messages=formatted_messages,
                    max_tokens=2048,
                    temperature=0.7,
                    timeout=60
                )
                return index, completion.choices[0].message.content
                
            except Exception as e:
                error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
                print(f"Index {index}, {error_msg}")
                
                if attempt == max_retries - 1:
                    # 最后一次尝试失败，返回错误
                    return index, f"[ERROR] {error_msg}"
                else:
                    # 重试前等待
                    time.sleep(2 ** attempt)  # 指数退避


def prepare_test_data(test_file: str):
    raw_data = []
    with open(test_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    # prompt, response
    test_data = []
    for item in tqdm(raw_data, desc="Preparing test data"):
        prompt = item["prompt"]
        test_data.append({
            "prompt": prompt,
        })
    return test_data


def main(test_file: str, output_file: str, num_actors: int = 8):
    test_data = prepare_test_data(test_file)
    
    actors = [InferenceActor.remote() for _ in range(num_actors)]
    pool = ray.util.ActorPool(actors)

    prompts_with_indices = [(i, item["prompt"]) for i, item in enumerate(test_data)]
    
    results_iterator = pool.map_unordered(lambda a, v: a.inference.remote(v[0], v[1]), prompts_with_indices)
    
    success_count = 0
    error_count = 0
    
    for index, response in tqdm(results_iterator, total=len(test_data), desc="Inferring Base Model"):
        test_data[index]["response"] = response
        if response.startswith("[ERROR]"):
            error_count += 1
        else:
            success_count += 1

    print(f"完成推理: 成功 {success_count} 个, 失败 {error_count} 个")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    ray.init(ignore_reinit_error=True)
    num_workers = 8  # 减少并发数避免过载
    file_path_list = [
        "/aifs4su/yaodong/boyuan/june_aligner/test_dataset/beavertails",
        "/aifs4su/yaodong/boyuan/june_aligner/test_dataset/harmfulqa",
    ]
    for file_path in file_path_list:
        test_file = os.path.join(file_path, "test_questions.json")
        
        output_file = os.path.join(file_path, model_name, "test_qa.json")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        main(test_file=test_file, output_file=output_file, num_actors=num_workers)
