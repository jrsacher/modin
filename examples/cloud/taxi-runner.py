# Licensed to Modin Development Team under one or more contributor license agreements.
# See the NOTICE file distributed with this work for additional information regarding
# copyright ownership.  The Modin Development Team licenses this file to you under the
# Apache License, Version 2.0 (the "License"); you may not use this file except in
# compliance with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.


# pip install git+https://github.com/intel-ai/ibis.git@develop
# pip install braceexpand

# NOTE: expects https://github.com/intel-ai/omniscripts checked out and in PYTHONPATH

import sys

USE_OMNISCI = "--omnisci" in sys.argv

# the following import turns on experimental mode in Modin,
# including enabling running things in remote cloud
import modin.experimental.pandas as pd  # noqa: F401
from modin.experimental.cloud import create_cluster

from taxi import run_benchmark as run_benchmark

cluster_params = {}
if USE_OMNISCI:
    cluster_params["cluster_type"] = "omnisci"
test_cluster = create_cluster(
    "aws",
    "aws_credentials",
    cluster_name="rayscale-test",
    region="eu-central-1",
    zone="eu-central-1b",
    image="ami-05f7491af5eef733a",
    **cluster_params,
)
with test_cluster:
    if USE_OMNISCI:
        from modin.experimental.cloud import get_connection

        # We should move omniscripts trigger in remote conext
        # https://github.com/intel-ai/omniscripts/blob/7d4599bcacf51de876952c658048571d32275ac1/taxi/taxibench_pandas_ibis.py#L482
        import modin.experimental.engines.omnisci_on_native.frame.omnisci_worker

        OmnisciServer = (
            get_connection()
            .modules["modin.experimental.engines.omnisci_on_native.frame.omnisci_worker"]
            .OmnisciServer
        )
        modin.experimental.engines.omnisci_on_native.frame.omnisci_worker.OmnisciServer = (
            OmnisciServer
        )

        # Omniscripts check for files being present when given local file paths,
        # so replace "glob" there with a remote one
        import utils.utils

        utils.utils.glob = get_connection().modules["glob"]

    parameters = {
        "data_file": "s3://modin-datasets/cloud/taxi/trips_xaa.csv",
        "dfiles_num": 1,
        "validation": False,
        "no_ibis": True,
        "no_pandas": False,
        "pandas_mode": "Modin_on_omnisci" if USE_OMNISCI else "Modin_on_ray",
        "ray_tmpdir": "/tmp",
        "ray_memory": 1024 * 1024 * 1024,
    }

    run_benchmark(parameters)
