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
"""
#################train MMoE example on census-income data########################
python train.py
"""

from mindspore import context
from mindspore.communication.management import init
from mindspore.context import ParallelMode
from mindspore.nn.optim import Adam
from mindspore.train.model import Model
from mindspore.train.callback import LossMonitor, TimeMonitor, ModelCheckpoint, CheckpointConfig
from mindspore.nn.wrap.loss_scale import DynamicLossScaleUpdateCell
from mindspore.common import set_seed

from src.mmoe import TrainStepWrap
from src.model_utils.moxing_adapter import moxing_wrapper
from src.load_dataset import create_dataset
from src.mmoe import MMoE_Layer
from src.model_utils.config import config
from src.mmoe import LossForMultiLabel, NetWithLossClass
from src.model_utils.device_adapter import get_device_id, get_device_num, get_rank_id, get_job_id
from src.get_lr import get_lr

set_seed(1)


def modelarts_pre_process():
    pass


@moxing_wrapper(pre_process=modelarts_pre_process)
def run_train():
    """train function"""
    print('device id:', get_device_id())
    print('device num:', get_device_num())
    print('rank id:', get_rank_id())
    print('job id:', get_job_id())

    device_target = config.device_target
    context.set_context(mode=context.GRAPH_MODE, device_target=config.device_target)
    context.set_context(save_graphs=False)
    if config.device_target == "GPU":
        context.set_context(enable_graph_kernel=True)
        context.set_context(graph_kernel_flags="--enable_cluster_ops=MatMul")

    device_num = get_device_num()

    if config.run_distribute:
        context.reset_auto_parallel_context()
        context.set_auto_parallel_context(device_num=device_num,
                                          parallel_mode=ParallelMode.DATA_PARALLEL, gradients_mean=True)
        if device_target == "Ascend":
            context.set_context(device_id=get_device_id())
            init()
        elif device_target == "GPU":
            init()
    else:
        context.set_context(device_id=get_device_id())
    print("init finished.")

    ds_train = create_dataset(config.data_path, config.batch_size, training=True, \
        target=config.device_target, run_distribute=config.run_distribute)

    if ds_train.get_dataset_size() == 0:
        raise ValueError("Please check dataset size > 0 and batch_size <= dataset size.")
    print("create dataset finished.")

    net = MMoE_Layer(input_size=config.num_features, num_experts=config.num_experts, units=config.units)
    print("model created.")
    loss = LossForMultiLabel()
    loss_net = NetWithLossClass(net, loss)

    step_per_size = ds_train.get_dataset_size()
    print("train dataset size:", step_per_size)

    if config.run_distribute:
        learning_rate = get_lr(0.0005, config.epoch_size, step_per_size, step_per_size * 2)
    else:
        learning_rate = get_lr(0.001, config.epoch_size, step_per_size, step_per_size * 5)
    opt = Adam(net.trainable_params(),
               learning_rate=learning_rate,
               beta1=0.9,
               beta2=0.999,
               eps=1e-7,
               weight_decay=0.0,
               loss_scale=1.0)
    scale_update_cell = DynamicLossScaleUpdateCell(loss_scale_value=2 ** 12,
                                                   scale_factor=2,
                                                   scale_window=1000)
    train_net = TrainStepWrap(loss_net, opt, scale_update_cell)
    train_net.set_train()
    model = Model(train_net)

    time_cb = TimeMonitor()
    loss_cb = LossMonitor(step_per_size)
    config_ck = CheckpointConfig(save_checkpoint_steps=step_per_size, keep_checkpoint_max=100)
    callbacks_list = [time_cb, loss_cb]
    if get_rank_id() == 0:
        ckpoint_cb = ModelCheckpoint(prefix='MMoE_train', directory=config.ckpt_path, config=config_ck)
        callbacks_list.append(ckpoint_cb)

    print("train start!")
    model.train(epoch=config.epoch_size,
                train_dataset=ds_train,
                callbacks=callbacks_list,
                dataset_sink_mode=config.dataset_sink_mode)


if __name__ == '__main__':
    run_train()
