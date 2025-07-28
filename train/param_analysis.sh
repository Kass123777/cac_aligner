python train/param_analysis.py \
    --lora_adapter_path ./LLaMA-Factory/saves/gemma3-1b/lora/lora_aligner_sft_r4_epoch3/adapter_model.safetensors \
    --base_model_path /aifs4su/yaodong/models/google/gemma-3-1b-it \
    --upstream_model_path /aifs4su/yaodong/models/meta-llama/Llama-2-70b-hf
