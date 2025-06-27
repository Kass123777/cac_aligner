# June Aligner 评估系统

本评估系统提供了对 June Aligner 对齐效果的全面评估，包括安全性（伦理道德）和有用性（通用能力）两个维度的偏序评价。

## 📁 文件结构

```
evaluation/
├── constant.py              # 评估提示词常量
├── api_text.py              # 文本API调用工具
├── api_multimodal.py        # 多模态API调用工具
├── ethics_evaluate.py       # 伦理道德评估脚本
├── general_benchmark.py     # 通用能力评估脚本
├── generate_report.py       # 报告生成脚本
└── README.md               # 使用说明
```

## 🚀 快速开始

### 步骤 1: 伦理道德评估（安全性）

```bash
# 指定具体实验
python3 ethics_evaluate.py \
    --api_key "your-api-key" \
    --api_base "https://api.example.com/v1/chat/completions" \
    --eval_model "gpt-4" \
    --test_dataset "beavertails" \
    --base_model "llama_sft_70b_slice_2167" \
    --aligner_name "lora_aligner_sft_r4_epoch3" \
    --output_dir "./eval_results"

# 或自动发现所有实验
python3 ethics_evaluate.py \
    --api_key "your-api-key" \
    --api_base "https://api.example.com/v1/chat/completions" \
    --eval_model "gpt-4" \
    --auto_discover \
    --output_dir "./eval_results"
```

### 步骤 2: 通用能力评估（有用性）

```bash
# 指定具体实验
python3 general_benchmark.py \
    --api_key "your-api-key" \
    --api_base "https://api.example.com/v1/chat/completions" \
    --eval_model "gpt-4" \
    --test_dataset "beavertails" \
    --base_model "llama_sft_70b_slice_2167" \
    --aligner_name "lora_aligner_sft_r4_epoch3" \
    --output_dir "./eval_results"

# 或自动发现所有实验
python3 general_benchmark.py \
    --api_key "your-api-key" \
    --api_base "https://api.example.com/v1/chat/completions" \
    --eval_model "gpt-4" \
    --auto_discover \
    --output_dir "./eval_results"
```

### 步骤 3: 生成综合报告

```bash
python3 generate_report.py \
    --results_dir "./eval_results" \
    --output_dir "./reports" \
    --output "alignment_report.md"
```

## 📋 详细说明

### ethics_evaluate.py - 伦理道德评估

**功能**: 评估对齐前后回答的安全性，判断哪个回答更无害。

**参数说明**:
- `--api_key`: 评估模型的API密钥（必需）
- `--api_base`: API基础URL（必需）
- `--eval_model`: 评估模型名称（必需）
- `--output_dir`: 输出目录（默认: `./eval_results`）
- `--inference_results_dir`: 推理结果目录（默认: `/aifs4su/yaodong/boyuan/june_aligner/inference_results`）
- `--test_dataset`: 测试数据集名称（如: beavertails, harmfulqa）
- `--base_model`: 基础模型名称（如: llama_sft_70b_slice_2167）
- `--aligner_name`: 对齐器名称（如: lora_aligner_sft_r4_epoch3）
- `--auto_discover`: 自动发现所有测试文件（与上述三个参数二选一）
- `--model_path`: 对齐模型路径（参考用）
- `--test_data`: 测试数据目录（参考用）
- `--baseline`: 基线模型路径（参考用）

**输出文件**:
- `safety_[实验名].json`: 单个实验的详细结果
- `safety_evaluation_summary.json`: 所有实验的汇总结果

**评估指标**:
- `safety_improvement_rate`: 安全性改进率（对齐后更安全的比例）
- `original_safer_rate`: 原始回答更安全的比例
- `equal_rate`: 安全性相同的比例

### general_benchmark.py - 通用能力评估

**功能**: 评估对齐前后回答的有用性，判断哪个回答更有帮助。

**参数说明**: 与 ethics_evaluate.py 相同

**输出文件**:
- `utility_[实验名].json`: 单个实验的详细结果
- `utility_evaluation_summary.json`: 所有实验的汇总结果

**评估指标**:
- `utility_improvement_rate`: 有用性改进率（对齐后更有用的比例）
- `utility_retention_rate`: 有用性保持率（保持或提升有用性的比例）
- `original_better_rate`: 原始回答更好的比例
- `equal_rate`: 有用性相同的比例

### generate_report.py - 报告生成

**功能**: 汇总安全性和有用性评估结果，生成综合分析报告。

**参数说明**:
- `--results_dir`: 评估结果目录（必需）
- `--output_dir`: 报告输出目录（默认: `./reports`）
- `--output`: 报告文件名（默认: `alignment_report.md`）

**输出文件**:
- `alignment_report.md`: Markdown格式的综合报告
- `evaluation_summary.csv`: CSV格式的汇总表格
- `evaluation_charts.png`: 可视化图表

## 🔧 配置说明

### API配置

在使用前需要配置评估模型的API信息：

```bash
# 示例配置
API_KEY="sk-ZA45vUH6dDT89S5XwYpwLbL6JtD4cdZrhqtaEJrIBcX7ffFn"
API_BASE="https://api3.xhub.chat/v1/chat/completions" 
EVAL_MODEL="gpt-4o"
```

### 数据格式

评估系统自动处理以下格式的数据：

```json
[
    {
        "prompt": "用户处理后的提示",
        "raw_data": {
            "raw_prompt": "原始用户提示",
            "original_answer": "基础模型的原始回答"
        },
        "correction": "对齐器校正后的回答"
    }
]
```

### 评估逻辑

1. **安全性评估**: 比较原始回答 vs 校正后回答的无害性
   - responseA = 原始回答
   - responseB = 校正后回答
   - 使用 `SAFETY_SCORE_SYSTEM_PROMPT` 进行评估

2. **有用性评估**: 比较原始回答 vs 校正后回答的有用性
   - responseA = 原始回答  
   - responseB = 校正后回答
   - 使用 `UTILITY_SCORE_SYSTEM_PROMPT` 进行评估

## 📊 结果解读

### 关键指标

- **安全性改进率**: 对齐后回答更安全的比例，越高越好
- **有用性改进率**: 对齐后回答更有用的比例，适中为好
- **有用性保持率**: 保持或提升有用性的比例，越高越好

### 理想结果

- 安全性改进率 > 70%：表明对齐显著提升了安全性
- 有用性保持率 > 80%：表明对齐没有显著损害有用性
- 有用性改进率 20-40%：适度的有用性提升，避免过度对齐

## 🎯 使用示例

### 方式一：指定具体实验

```bash
# 1. 设置环境变量
export API_KEY="your-api-key"
export API_BASE="https://api.openai.com/v1/chat/completions"
export EVAL_MODEL="gpt-4"

# 2. 运行安全性评估
python3 ethics_evaluate.py \
    --api_key $API_KEY \
    --api_base $API_BASE \
    --eval_model $EVAL_MODEL \
    --test_dataset "beavertails" \
    --base_model "llama_sft_70b_slice_2167" \
    --aligner_name "lora_aligner_sft_r4_epoch3" \
    --output_dir ./eval_results

# 3. 运行有用性评估  
python3 general_benchmark.py \
    --api_key $API_KEY \
    --api_base $API_BASE \
    --eval_model $EVAL_MODEL \
    --test_dataset "beavertails" \
    --base_model "llama_sft_70b_slice_2167" \
    --aligner_name "lora_aligner_sft_r4_epoch3" \
    --output_dir ./eval_results

# 4. 生成综合报告
python3 generate_report.py \
    --results_dir ./eval_results \
    --output_dir ./reports \
    --output alignment_report.md
```

### 方式二：自动发现所有实验

```bash
# 1. 设置环境变量
export API_KEY="your-api-key"
export API_BASE="https://api.openai.com/v1/chat/completions"
export EVAL_MODEL="gpt-4"

# 2. 运行安全性评估（自动发现）
python3 ethics_evaluate.py \
    --api_key $API_KEY \
    --api_base $API_BASE \
    --eval_model $EVAL_MODEL \
    --auto_discover \
    --output_dir ./eval_results

# 3. 运行有用性评估（自动发现）
python3 general_benchmark.py \
    --api_key $API_KEY \
    --api_base $API_BASE \
    --eval_model $EVAL_MODEL \
    --auto_discover \
    --output_dir ./eval_results

# 4. 生成综合报告
python3 generate_report.py \
    --results_dir ./eval_results \
    --output_dir ./reports \
    --output alignment_report.md
```

### 方式三：使用bash脚本

```bash
# 运行简化示例
./simple_example.sh

# 或运行批量评估
./batch_evaluation.sh
```

### 批量评估脚本

```bash
#!/bin/bash
# batch_evaluation.sh

set -e

API_KEY="sk-ZA45vUH6dDT89S5XwYpwLbL6JtD4cdZrhqtaEJrIBcX7ffFn"
API_BASE="https://api3.xhub.chat/v1/chat/completions"
EVAL_MODEL="gpt-4o"
OUTPUT_DIR="./eval_results_$(date +%Y%m%d_%H%M%S)"

echo "开始评估..."
echo "输出目录: $OUTPUT_DIR"

# 安全性评估
echo "执行安全性评估..."
python3 ethics_evaluate.py \
    --api_key "$API_KEY" \
    --api_base "$API_BASE" \
    --eval_model "$EVAL_MODEL" \
    --output_dir "$OUTPUT_DIR"

# 有用性评估
echo "执行有用性评估..."
python3 general_benchmark.py \
    --api_key "$API_KEY" \
    --api_base "$API_BASE" \
    --eval_model "$EVAL_MODEL" \
    --output_dir "$OUTPUT_DIR"

# 生成报告
echo "生成报告..."
python3 generate_report.py \
    --results_dir "$OUTPUT_DIR" \
    --output_dir "$OUTPUT_DIR/reports" \
    --output "alignment_report_$(date +%Y%m%d).md"

echo "评估完成! 结果保存在: $OUTPUT_DIR"
```

## 🛠️ 依赖要求

```bash
pip install pandas matplotlib seaborn ray requests tqdm
```

## ⚠️ 注意事项

1. **API调用成本**: 评估过程会产生大量API调用，请注意成本控制
2. **缓存机制**: 系统自动缓存评估结果，重复运行会跳过已评估的样本
3. **并发控制**: 默认并发数为20，可根据API限制调整
4. **错误处理**: 系统会自动重试失败的API调用，最多重试3次

## 🔍 故障排除

### 常见问题

1. **API调用失败**: 检查API密钥和网络连接
2. **内存不足**: 减少并发数或分批处理
3. **文件路径错误**: 确认推理结果文件路径正确
4. **权限问题**: 确保脚本有执行权限

### 获取帮助

```bash
python3 ethics_evaluate.py --help
python3 general_benchmark.py --help  
python3 generate_report.py --help
```

---

**更多技术支持**, 请联系项目维护团队。 