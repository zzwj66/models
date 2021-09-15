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

if [ $# != 4 ]; then
  echo "Usage: ./scripts/run_eval.sh [device ID] [ckpt path] [annot path] [image path]"
  exit 1
fi

export DEVICE_ID=$1
PATH_CHECKPOINT=$2
ANNOT_DIR=$3
IMG_DIR=$4

TARGET="./Eval"

rm -rf $TARGET
mkdir $TARGET
cp *.py $TARGET
cp -r src $TARGET

cd $TARGET

nohup python eval.py  \
    --ckpt_file=$PATH_CHECKPOINT  \
    --annot_dir=$ANNOT_DIR  \
    --img_dir=$IMG_DIR > result.txt 2> err.txt &
