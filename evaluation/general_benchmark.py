#!/usr/bin/env python3
"""General Capability and Helpfulness Evaluation Script"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import re

from api_text import batch_process_text_api
from constant import UTILITY_SCORE_SYSTEM_PROMPT, UTILITY_SCORE_USER_PROMPT

def load_test_data(file_path: str) -> List[Dict]:
    """加载测试数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_path_info(file_path: str) -> Tuple[str, str, str]:
    """从文件路径提取信息"""
    # 例如: /path/to/inference_results/beavertails/llama_sft_70b_slice_2167/lora_aligner_sft_r4_epoch3/test_data_aligned.json
    parts = Path(file_path).parts
    for i, part in enumerate(parts):
        if part == 'inference_results':
            test_dataset = parts[i + 1]
            base_model = parts[i + 2]
            aligner_name = parts[i + 3]
            return test_dataset, base_model, aligner_name
    raise ValueError(f"Cannot extract info from path: {file_path}")

def find_all_test_files(base_dir: str) -> List[str]:
    """查找所有test_data_aligned.json文件"""
    test_files = []
    base_path = Path(base_dir)
    
    for file_path in base_path.rglob("test_data_aligned.json"):
        test_files.append(str(file_path))
    
    return test_files

def parse_utility_result(result: str) -> str:
    """解析有用性评估结果"""
    result_lower = result.lower()
    
    # 首先检查是否包含 responseA 或 responseB
    if "responsea" in result_lower:
        return "responseA"
    elif "responseb" in result_lower:
        return "responseB"
    elif "equal" in result_lower:
        return "Equal"
    
    # 备用方案：查找 "Better: [[...]]" 模式
    pattern = r"Better: \[\[(.+?)\]\]"
    match = re.search(pattern, result, re.IGNORECASE)
    if match:
        matched_result = match.group(1).lower()
        if "responsea" in matched_result:
            return "responseA"
        elif "responseb" in matched_result:
            return "responseB"
        elif "equal" in matched_result:
            return "Equal"
        return match.group(1)
    
    return "Unknown"

def evaluate_utility_batch(
    test_data: List[Dict],
    api_key: str,
    api_base: str,
    model: str,
    cache_dir: str = './cache/utility'
) -> List[Dict]:
    """批量进行有用性评估"""
    
    system_prompts = []
    user_prompts = []
    
    for item in test_data:
        prompt = item['raw_data']['raw_prompt']
        response_a = item['correction']  # 对齐后回答
        response_b = item['raw_data']['original_answer']  # 原始回答
        
        system_prompts.append(UTILITY_SCORE_SYSTEM_PROMPT)
        user_prompts.append(UTILITY_SCORE_USER_PROMPT.format(
            prompt=prompt,
            responseA=response_a,
            responseB=response_b
        ))
    
    # 批量调用API
    results = batch_process_text_api(
        system_prompts,
        user_prompts,
        api_key=api_key,
        api_base=api_base,
        model=model,
        cache_dir=cache_dir,
        num_workers=20
    )
    
    # 解析结果
    evaluation_results = []
    for i, (item, result) in enumerate(zip(test_data, results)):
        utility_winner = parse_utility_result(result)
        
        evaluation_results.append({
            'index': i,
            'prompt': item['raw_data']['raw_prompt'],
            'original_answer': item['raw_data']['original_answer'],
            'corrected_answer': item['correction'],
            'utility_evaluation': result,
            'utility_winner': utility_winner,  # responseA(对齐后)/responseB(原始)/Equal
        })
    
    return evaluation_results

def calculate_utility_metrics(results: List[Dict]) -> Dict:
    """计算有用性指标"""
    total = len(results)
    response_a_wins = sum(1 for r in results if r['utility_winner'] == 'responseA')
    response_b_wins = sum(1 for r in results if r['utility_winner'] == 'responseB')
    equal_cases = sum(1 for r in results if r['utility_winner'] == 'Equal')
    unknown_cases = sum(1 for r in results if r['utility_winner'] == 'Unknown')
    
    return {
        'total_samples': total,
        'original_better': response_b_wins,  # responseB现在是原始答案
        'corrected_better': response_a_wins,  # responseA现在是对齐后答案
        'equal_utility': equal_cases,
        'unknown': unknown_cases,
        'utility_improvement_rate': (response_a_wins - response_b_wins) / total if total > 0 else 0,  # (corrected_better - original_better) / total
        'original_better_rate': response_b_wins / total if total > 0 else 0,  # responseB是原始答案
        'equal_rate': equal_cases / total if total > 0 else 0,
        'utility_retention_rate': (response_a_wins + equal_cases) / total if total > 0 else 0  # 保持或提升有用性的比例
    }

def main():
    parser = argparse.ArgumentParser(description='General Capability and Helpfulness Evaluation')
    # parser.add_argument('--model_path', type=str, help='Path to aligned model (for reference)')
    # parser.add_argument('--baseline', type=str, help='Path to baseline model (for reference)')
    parser.add_argument('--api_key', type=str, required=False, help='API key for evaluation model', default='sk-ZA45vUH6dDT89S5XwYpwLbL6JtD4cdZrhqtaEJrIBcX7ffFn')
    parser.add_argument('--api_base', type=str, required=False, help='API base URL', default='https://api3.xhub.chat/v1/chat/completions')
    parser.add_argument('--eval_model', type=str, required=False, help='Evaluation model name', default='gpt-4o')
    parser.add_argument('--output_dir', type=str, default='./eval_results', help='Output directory')
    parser.add_argument('--inference_results_dir', type=str, 
                       default='/aifs4su/yaodong/boyuan/june_aligner/inference_results',
                       help='Inference results directory')
    
    # 新增参数：指定具体的实验配置
    parser.add_argument('--test_data', type=str, help='Test dataset name (e.g., beavertails, harmfulqa)')
    parser.add_argument('--baseline', type=str, help='Base model name (e.g., llama_sft_70b_slice_2167)')
    parser.add_argument('--model_path', type=str, help='Aligner name (e.g., lora_aligner_sft_r4_epoch3)')
    parser.add_argument('--auto_discover', action='store_true', help='Auto discover all test files')
    
    args = parser.parse_args()
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 确定测试文件列表
    test_files = []
    if args.auto_discover:
        # 自动发现所有测试文件
        test_files = find_all_test_files(args.inference_results_dir)
        print(f"自动发现 {len(test_files)} 个测试文件")
    else:
        # 根据指定参数构建文件路径
        if not all([args.test_data, args.baseline, args.model_path]):
            print("错误：必须提供 --test_data, --baseline, --model_path 参数，或使用 --auto_discover")
            return
        
        test_file = os.path.join(
            args.inference_results_dir,
            args.test_data,
            args.baseline,
            args.model_path,
            "test_data_aligned.json"
        )
        
        if os.path.exists(test_file):
            test_files = [test_file]
            # print(f"使用指定文件: {test_file}")
        else:
            # print(f"错误：文件不存在 {test_file}")
            return
    
    all_results = {}
    
    for test_file in test_files:
        # print(f"\n处理文件: {test_file}")
        
        try:
            # 提取路径信息
            test_dataset, base_model, aligner_name = extract_path_info(test_file)
            print(f"  测试数据集: {test_dataset}")
            print(f"  基础模型: {base_model}")
            print(f"  对齐器: {aligner_name}")
            
            # 加载数据
            test_data = load_test_data(test_file)
            print(f"  加载了 {len(test_data)} 个测试样本")
            
            # 进行有用性评估
            cache_dir = f"{args.output_dir}/cache/utility/{test_dataset}_{base_model}_{aligner_name}"
            evaluation_results = evaluate_utility_batch(
                test_data,
                args.api_key,
                args.api_base,
                args.eval_model,
                cache_dir
            )
            
            # 计算指标
            metrics = calculate_utility_metrics(evaluation_results)
            
            # 保存结果
            result_key = f"{test_dataset}_{base_model}_{aligner_name}"
            all_results[result_key] = {
                'test_dataset': test_dataset,
                'base_model': base_model,
                'aligner_name': aligner_name,
                'file_path': test_file,
                'metrics': metrics,
                'detailed_results': evaluation_results
            }
            
            # 保存单个结果文件
            output_file = f"{args.output_dir}/utility_{result_key}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results[result_key], f, ensure_ascii=False, indent=2)
            
            print(f"  有用性改进率: {metrics['utility_improvement_rate']:.2%}")
            # print(f"  有用性保持率: {metrics['utility_retention_rate']:.2%}")
            print(f"  结果已保存到: {output_file}")
            
        except Exception as e:
            print(f"  处理文件时出错: {e}")
            continue
    
    # 保存汇总结果
    summary_file = f"{args.output_dir}/utility_evaluation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n所有结果已保存到: {summary_file}")
    
    # 打印汇总统计
    print("\n=== 有用性评估汇总 ===")
    for key, result in all_results.items():
        metrics = result['metrics']
        print(f"{key}:")
        print(f"  有用性改进率: {metrics['utility_improvement_rate']:.2%}")
        # print(f"  有用性保持率: {metrics['utility_retention_rate']:.2%}")
        print(f"  样本总数: {metrics['total_samples']}")
        print(f"  对齐后更好: {metrics['corrected_better']}")
        # print(f"  原始更好: {metrics['original_better']}")
        # print(f"  有用性相同: {metrics['equal_utility']}")

if __name__ == '__main__':
    main() 