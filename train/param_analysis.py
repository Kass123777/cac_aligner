from safetensors.torch import load_file
import os
import argparse

# lora_adapter_path = '/home/yangyaodong/cac_aligner/LLaMA-Factory/saves/gemma3-1b/lora/sft-r4/adapter_model.safetensors'
# base_model_path = '/aifs4su/yaodong/models/google/gemma-3-1b-it'
# upstream_model_path = '/aifs4su/yaodong/models/meta-llama/Llama-2-70b-hf'

def parse_args():
    parser = argparse.ArgumentParser(description='分析模型参数量')
    parser.add_argument('--lora_adapter_path', type=str, required=True,
                       help='LoRA adapter模型路径')
    parser.add_argument('--base_model_path', type=str, required=True,
                       help='基础模型路径')
    parser.add_argument('--upstream_model_path', type=str, required=True,
                       help='上游模型路径')
    return parser.parse_args()

def main():
    args = parse_args()

    # 加载upstream model 权重
    upstream_params = 0
    for safetensors_path in os.listdir(args.upstream_model_path):
        if safetensors_path.endswith('.safetensors'):
            state_dict = load_file(os.path.join(args.upstream_model_path, safetensors_path))
            for k, v in state_dict.items():
                num_params = v.numel()
                # print(f"{k}: {num_params}")
                upstream_params += num_params

    print(f"原始模型总参数量: {upstream_params / 1e9:.4f}B")

    # 加载 LoRA adapter 权重
    state_dict = load_file(args.lora_adapter_path)

    trained_params = 0
    for k, v in state_dict.items():
        num_params = v.numel()
        trained_params += num_params

    # 加载 base model 权重
    base_params = 0
    for safetensors_path in os.listdir(args.base_model_path):
        if safetensors_path.endswith('.safetensors'):
            state_dict = load_file(os.path.join(args.base_model_path, safetensors_path))
            for k, v in state_dict.items():
                num_params = v.numel()
                # print(f"{k}: {num_params}")
                base_params += num_params

    print(f"对齐后总参数量: {(trained_params + base_params + upstream_params) / 1e9:.4f}B")
    print(f"训练参数量: {trained_params / 1e9:.4f}B")
    print(f"非训练新增参数量: {(base_params) / 1e9:.4f}B")

    # 计算参数效率
    print(f"参数效率（训练参数量/原始模型参数量）: {trained_params / upstream_params * 100:.4f}%")

if __name__ == "__main__":
    main()
