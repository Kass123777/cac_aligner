MODEL_PATH=/aifs4su/hansirui_1st/boyuan/llama_sft_70b/slice_2167
TEMPLATE_PATH=/aifs4su/yaodong/boyuan/june_aligner/lora_inference/template_alpaca.jinja
export VLLM_USE_V1=0
export BASE_MODEL_PORT=8012
export BASE_MODEL_API_KEY=base_model

export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
vllm serve $MODEL_PATH \
    --port $BASE_MODEL_PORT \
    --host 0.0.0.0 \
    --dtype auto \
    --max-model-len 4096 \
    --tensor-parallel-size 8 \
    --gpu-memory-utilization 0.9 \
    --api-key $BASE_MODEL_API_KEY \
    --chat-template $TEMPLATE_PATH
