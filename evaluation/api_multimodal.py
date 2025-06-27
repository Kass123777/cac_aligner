"""Evaluate assistant's response harmlessness and helpfulness with multimodal capabilities"""

from __future__ import annotations
import os
import hashlib
import logging
import time
import json
import base64
from typing import Any, Callable
from io import BytesIO

import ray
import requests
from tqdm import tqdm
from PIL import Image

def encode_image(image_path: str) -> str:
    """Convert image to base64 encoded string"""
    image_input = Image.open(image_path)
    
    if image_input.mode != "RGB":
        image_input = image_input.convert("RGB")

    buffer = BytesIO()
    image_input.save(buffer, format="JPEG")
    img_bytes = buffer.getvalue()
    base64_data = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_data}"

@ray.remote(num_cpus=1)
def call_multimodal_api(
    system_content: str,
    user_content: str,
    image_path: str = None,
    temperature: float = 0.2,
    post_process: Callable = lambda x: x,
    api_key: str = None,
    api_base: str = None,
    model: str = None,
) -> Any:
    """Call multimodal API with text and optional image"""
    
    messages = [
        {'role': 'system', 'content': system_content},
        {'role': 'user', 'content': []}
    ]
    
    # Add image if provided
    if image_path:
        messages[1]['content'].append(
            {"type": "image_url", "image_url": {"url": encode_image(image_path)}}
        )
    
    # Add text content
    messages[1]['content'].append({"type": "text", "text": user_content})
    
    max_retries = 3
    
    while max_retries > 0:
        try:
            response = requests.post(
                api_base,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature
                },
            )
            
            if response.status_code == 200:
                response_text = response.json()['choices'][0]['message']['content']
                logging.info(response_text)
                return post_process(response_text)
            else:
                logging.error(f"API error: {response.status_code} - {response.text}")
                time.sleep(3)
                max_retries -= 1
        except Exception as e:
            logging.error(f"Exception: {str(e)}")
            time.sleep(3)
            max_retries -= 1
    
    logging.error('API call failed after multiple attempts')
    return ""

def generate_hash_uid(to_hash: dict | tuple | list | str) -> str:
    """Generate unique hash for caching"""
    json_string = json.dumps(to_hash, sort_keys=True)
    hash_object = hashlib.sha256(json_string.encode())
    return hash_object.hexdigest()

def batch_process_api(
    system_contents: list[str],
    user_contents: list[str],
    image_paths: list[str] = None,
    num_workers: int = 50,
    post_process: Callable = lambda x: x,
    temperature: list[float] | float = None,
    cache_dir: str = './cache',
    api_key: str = None,
    api_base: str = None,
    model: str = None,
) -> list:
    """Process multiple API calls in parallel with caching"""
    if len(system_contents) != len(user_contents):
        raise ValueError('Length of system_contents and user_contents must be equal')
    
    # Ensure cache directory exists
    os.makedirs(cache_dir, exist_ok=True)
    
    # Initialize Ray for parallel processing
    ray.init()
    
    # Prepare parameters and tracking variables
    if image_paths is None:
        image_paths = [None] * len(system_contents)
    
    if temperature is None:
        temperature = [0.2] * len(system_contents)
    elif isinstance(temperature, float):
        temperature = [temperature] * len(system_contents)
    
    contents = list(enumerate(zip(system_contents, user_contents, image_paths)))
    results = [None] * len(system_contents)
    api_calls = 0
    
    # Generate cache UIDs
    uids = [
        generate_hash_uid({
            'content': content,
            'temperature': temp,
            'model': model,
        }) for content, temp in zip(contents, temperature)
    ]
    
    # Setup progress tracking
    bar = tqdm(total=len(system_contents))
    not_finished = []
    
    # Process all items
    while True:
        if len(not_finished) == 0 and len(contents) == 0:
            break
            
        # Fill worker queue
        while len(not_finished) < num_workers and len(contents) > 0:
            index, content = contents.pop()
            uid = uids[index]
            temp = temperature[index]
            cache_path = os.path.join(cache_dir, f'{uid}.json')
            
            # Check cache first
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        results[index] = json.load(f)
                    bar.update(1)
                    continue
                except:
                    os.remove(cache_path)
            
            # Queue API call
            future = call_multimodal_api.remote(
                content[0],  # system prompt
                content[1],  # user prompt
                content[2],  # image path
                temp, 
                post_process,
                api_key,
                api_base,
                model,
            )
            not_finished.append([index, future])
            api_calls += 1
        
        if not not_finished:
            continue
        
        # Check for completed tasks
        indices, futures = zip(*not_finished)
        finished, not_finished_futures = ray.wait(list(futures), timeout=1.0)
        
        # Process completed tasks
        finished_indices = [indices[futures.index(task)] for task in finished]
        for i, task in enumerate(finished):
            idx = finished_indices[i]
            result = ray.get(task)
            results[idx] = result
            
            # Save to cache
            cache_path = os.path.join(cache_dir, f'{uids[idx]}.json')
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
        
        # Update not_finished list
        not_finished = [(index, future) for index, future in not_finished if future not in finished]
        bar.update(len(finished))
    
    bar.close()
    ray.shutdown()
    print(f'API calls made: {api_calls}')
    
    return results

if __name__ == '__main__':
    SYSTEM_PROMPT = """\
You are a reasoning model with advanced analytical capabilities. I will provide an image and ask a question about it. Your task is to analyze the image thoroughly and answer my question accurately.

Response format:
<think>
[step-by-step reasoning process]
</think>
[final answer]

Guidelines:
1. Place your reasoning process between <think> and </think> tags first, and then provide your answer.
2. The reasoning process can include expressions like "let me think," "oh, I see," or "maybe I should think about it from a different angle."
"""
    
    system_prompts = [SYSTEM_PROMPT]
    user_prompts = ["Describe the text in the image."]
    image_paths = ["path/to/your/image.png"]
    
    api_key = "your-api-key"
    api_base = "https://api.example.com/v1/chat/completions"
    model = "model-name"
    
    results = batch_process_api(
        system_prompts,
        user_prompts,
        image_paths,
        api_key=api_key,
        api_base=api_base,
        model=model,
    )
    
    for result in results:
        print(result)
