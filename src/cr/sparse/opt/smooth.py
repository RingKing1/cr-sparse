# Copyright 2021 CR.Sparse Development Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from cr.sparse._src.opt.smooth import (
    smooth_value_grad
)


from cr.sparse._src.opt.smooth.constant import smooth_constant
from cr.sparse._src.opt.smooth.entropy import (
    smooth_entropy,
    smooth_entropy_vg)
from cr.sparse._src.opt.smooth.huber import smooth_huber
from cr.sparse._src.opt.smooth.linear import smooth_linear