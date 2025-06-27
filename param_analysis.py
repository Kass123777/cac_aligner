from safetensors.torch import load_file
import os

lora_adapter_path = '/aifs4su/yaodong/cac_aligner/models/gemma3/gemma3-1b-lora/adapter_model.safetensors'
base_model_path = '/aifs4su/yaodong/models/google/gemma-3-1b-it'
upstream_model_path = '/aifs4su/yaodong/models/meta-llama/Llama-2-70b-hf'

# 加载upstream model 权重
upstream_params = 0
for safetensors_path in os.listdir(upstream_model_path):
    if safetensors_path.endswith('.safetensors'):
        state_dict = load_file(os.path.join(upstream_model_path, safetensors_path))
        for k, v in state_dict.items():
            num_params = v.numel()
            # print(f"{k}: {num_params}")
            upstream_params += num_params


print(f"原始模型总参数量: {upstream_params / 1e9:.4f}B")

# 加载 LoRA adapter 权重
state_dict = load_file(lora_adapter_path)

trained_params = 0
for k, v in state_dict.items():
    num_params = v.numel()
    trained_params += num_params


# 加载 base model 权重
base_params = 0
for safetensors_path in os.listdir(base_model_path):
    if safetensors_path.endswith('.safetensors'):
        state_dict = load_file(os.path.join(base_model_path, safetensors_path))
        for k, v in state_dict.items():
            num_params = v.numel()
            # print(f"{k}: {num_params}")
            base_params += num_params

print(f"对齐后总参数量: {(trained_params + base_params + upstream_params) / 1e9:.4f}B")
print(f"训练参数量: {trained_params / 1e9:.4f}B")
print(f"非训练新增参数量: {(base_params) / 1e9:.4f}B")

# 计算参数效率
print(f"参数效率（训练参数量/原始模型参数量）: {trained_params / upstream_params * 100:.4f}%")
