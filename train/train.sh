python train/alignment_train.py \
    --base_model /aifs4su/yaodong/models/google/gemma-3-1b-it \
    --train_data ./LLaMA-Factory/data/alpaca_qac_0618.json \
    --output_dir ./LLaMA-Factory/saves/gemma3-1b/lora/lora_aligner_sft_r4_epoch3 \
    --epochs 3 \
    --batch_size 16
