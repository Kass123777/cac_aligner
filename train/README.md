# 对齐训练模块

本模块用于执行大语言模型的对齐训练，基于LLaMA-Factory框架进行LoRA微调。

## 功能特性

- 支持LoRA微调训练
- 基于LLaMA-Factory框架
- 支持自定义训练参数
- 提供参数分析工具

## 文件说明

- `alignment_train.py`: 主要的对齐训练脚本
- `train.sh`: 训练启动脚本
- `param_analysis.py`: 参数分析工具
- `param_analysis.sh`: 参数分析启动脚本

## 快速开始

### 1. 执行训练

```bash
# 使用默认参数训练
bash train.sh

# 或直接运行Python脚本
python train/alignment_train.py \
    --base_model /path/to/base/model \
    --train_data ./path/to/train/data \
    --output_dir ./path/to/output \
    --epochs 3 \
    --batch_size 16
```

### 2. 参数分析

```bash
# 运行参数分析
bash param_analysis.sh
```

## 参数说明

- `--base_model`: 基础模型路径
- `--train_data`: 训练数据路径
- `--output_dir`: 输出模型保存路径
- `--epochs`: 训练轮次（默认3）
- `--batch_size`: 批次大小（默认16）

## 注意事项

1. 确保已正确安装LLaMA-Factory
2. 训练前请检查数据路径和模型路径是否正确
3. 根据硬件配置调整batch_size参数
4. 训练完成后模型将保存在指定的output_dir目录中

## 相关链接

- [主项目README](../README.md)
- [评估模块](../evaluation/README.md)
