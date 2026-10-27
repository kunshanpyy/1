#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../.."
python tools/train.py innovations/edge_aware_ukan/configs/ukan_light_refine_da_tr_vaihingen_stratified_quick.py
