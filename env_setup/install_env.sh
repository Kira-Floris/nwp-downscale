#!/bin/bash

# Create conda environment without asking for confirmation
conda env create --file ilan_env.yml -y

# Activate the conda environment
conda activate ilan

# Install pip without confirmation
conda install pip -y

# Deactivate and reactivate the environment to ensure pip is available
conda deactivate
conda deactivate
conda activate ilan

# Install packages from requirements file without confirmation
pip install -r ilan_env_requirements.txt

# Install specific versions of PyTorch and torchvision without confirmation
pip3 install torch==1.9.0+cu111 torchvision==0.10.0+cu111 -f https://download.pytorch.org/whl/torch_stable.html

# Create necessary directories for environment variables setup
mkdir -p /opt/conda/envs/ilan/etc/conda/activate.d
mkdir -p /opt/conda/envs/ilan/etc/conda/deactivate.d

# Create activation and deactivation scripts
touch /opt/conda/envs/ilan/etc/conda/activate.d/env_vars.sh
touch /opt/conda/envs/ilan/etc/conda/deactivate.d/env_vars.sh

# Add environment variable settings to activation script
echo '#!/bin/sh' >> /opt/conda/envs/ilan/etc/conda/activate.d/env_vars.sh
echo 'export OLD_LD_LIBRARY_PATH=${LD_LIBRARY_PATH}' >> /opt/conda/envs/ilan/etc/conda/activate.d/env_vars.sh
echo 'export LD_LIBRARY_PATH=/opt/conda/envs/ilan/lib/:${OLD_LD_LIBRARY_PATH}' >> /opt/conda/envs/ilan/etc/conda/activate.d/env_vars.sh

# Add environment variable reset to deactivation script
echo '#!/bin/sh' >> /opt/conda/envs/ilan/etc/conda/deactivate.d/env_vars.sh
echo 'export LD_LIBRARY_PATH=${OLD_LD_LIBRARY_PATH}' >> /opt/conda/envs/ilan/etc/conda/deactivate.d/env_vars.sh
echo 'unset OLD_LD_LIBRARY_PATH' >> /opt/conda/envs/ilan/etc/conda/deactivate.d/env_vars.sh

# Deactivate and reactivate the environment
conda deactivate
conda init
conda activate ilan
