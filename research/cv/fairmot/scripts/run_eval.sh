#!/bin/bash
# Copyright 2021 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
echo "========================================================================"
echo "Please run the script as: "
echo "bash run_eval.sh DEVICE_ID LOAD_MODEL(options)"
echo "For example: bash run_eval.sh 0 ./dla34.ckpt data_dir"
echo "It is better to use the absolute path."
echo "========================================================================"
export DEVICE_ID=$1
export LOAD_MODEL=$2
DATASET=$3
echo "start training for device $DEVICE_ID"
python -u ../fairmot_eval.py  --id=$DEVICE_ID --load_model=$LOAD_MODEL --data_dir $DATASET > eval_$DEVICE_ID.txt 2>&1 &
echo "finish"