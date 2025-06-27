python alignment_train.py \
    --base_model ./models/base_model/ \
    --train_data ./data/train.jsonl \
    --output_dir ./models/lora_aligner_sft_r4_epoch3 \
    --epochs 3 \
    --batch_size 16