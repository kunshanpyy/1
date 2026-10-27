#!/usr/bin/env bash
set -e

CONFIG="innovations/edge_aware_ukan/configs/ukan_multiscale_fusion_ablation_vaihingen.py"
GPUS="${CUDA_VISIBLE_DEVICES:-0}"
MODE="${1:-help}"

run_exp () {
  local NAME="$1"
  shift
  echo "[INFO] Running $NAME"
  CUDA_VISIBLE_DEVICES="$GPUS" python tools/train.py "$CONFIG" --cfg-options "$@"
}

case "$MODE" in
  base)
    run_exp "scheme3_base_384" \
      work_dir=./work_dirs/scheme3_base_384 \
      model.decode_head.da=False \
      model.decode_head.tr=False \
      img_size='(384,384)' crop_size='(384,384)' \
      data.samples_per_gpu=1 optimizer.lr=5e-4
    ;;

  tr)
    run_exp "scheme3_tr_384" \
      work_dir=./work_dirs/scheme3_tr_384 \
      model.decode_head.da=False \
      model.decode_head.tr=True \
      img_size='(384,384)' crop_size='(384,384)' \
      data.samples_per_gpu=1 optimizer.lr=5e-4
    ;;

  da)
    run_exp "scheme3_da_512" \
      work_dir=./work_dirs/scheme3_da_512 \
      model.decode_head.da=True \
      model.decode_head.tr=False \
      img_size='(512,512)' crop_size='(512,512)' \
      model.test_cfg.crop_size='(512,512)' model.test_cfg.stride='(256,256)' \
      data.samples_per_gpu=1 optimizer.lr=3e-4
    ;;

  all)
    run_exp "scheme3_da_tr_512" \
      work_dir=./work_dirs/scheme3_da_tr_512 \
      model.decode_head.da=True \
      model.decode_head.tr=True \
      img_size='(512,512)' crop_size='(512,512)' \
      model.test_cfg.crop_size='(512,512)' model.test_cfg.stride='(256,256)' \
      data.samples_per_gpu=1 optimizer.lr=3e-4
    ;;

  quick)
    run_exp "scheme3_quick_smoke" \
      work_dir=./work_dirs/scheme3_quick_smoke \
      model.decode_head.da=False \
      model.decode_head.tr=False \
      runner.max_iters=200 checkpoint_config.interval=200 evaluation.interval=200 \
      img_size='(384,384)' crop_size='(384,384)' \
      data.samples_per_gpu=1 optimizer.lr=5e-4
    ;;

  help|*)
    echo "Usage: bash innovations/edge_aware_ukan/run_scheme3_ablation.sh [base|tr|da|all|quick]"
    echo ""
    echo "base  : 方案3 仅模块本身（无 da, 无 tr），384 patch"
    echo "tr    : 方案3 + 改进2（tr=True），384 patch"
    echo "da    : 方案3 + 改进1（da=True），512 patch"
    echo "all   : 方案3 + 改进1 + 改进2，512 patch（最重，风险最高）"
    echo "quick : 200 iter 快速冒烟测试"
    ;;
esac
