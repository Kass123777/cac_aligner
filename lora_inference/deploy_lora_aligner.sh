MODEL_PATH=/aifs4su/yaodong/models/google/gemma-3-1b-it
LORA_PATH=/home/yangyaodong/cac_aligner/LLaMA-Factory/saves/gemma3-1b/lora/sft-r4-e3
export VLLM_USE_V1=0
export ALIGNER_PORT=8011
export ALIGNER_API_KEY=lora_aligner

export CUDA_VISIBLE_DEVICES=0,1,2,3
vllm serve $MODEL_PATH \
    --enable-lora \
    --lora-modules sql-lora=$LORA_PATH \
    --port $ALIGNER_PORT \
    --host 0.0.0.0 \
    --dtype auto \
    --max-model-len 4096 \
    --tensor-parallel-size 4 \
    --gpu-memory-utilization 0.9 \
    --api-key $ALIGNER_API_KEY