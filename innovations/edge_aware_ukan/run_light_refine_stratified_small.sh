#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../.."

python innovations/edge_aware_ukan/resplit_vaihingen_stratified.py \
  --src-root ./data/vaihingen \
  --dst-root ./data/vaihingen_stratified \
  --val-ratio 0.2 \
  --seed 42 \
  --copy-test-from-val

python innovations/edge_aware_ukan/build_small_vaihingen_subset.py \
  --src-root ./data/vaihingen_stratified \
  --dst-root ./data/vaihingen_stratified_small \
  --train-per-area 60 \
  --val-per-area 20 \
  --seed 42

python tools/train.py innovations/edge_aware_ukan/configs/ukan_light_refine_da_tr_vaihingen_stratified_small.py
