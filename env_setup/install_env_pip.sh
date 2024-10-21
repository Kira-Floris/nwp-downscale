#!/bin/bash

# Install necessary pip packages from requirements file
pip install -r ilan_env_requirements.txt
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Set up environment variable scripts
mkdir -p /etc/pip/activate.d
mkdir -p /etc/pip/deactivate.d
touch /etc/pip/activate.d/env_vars.sh
touch /etc/pip/deactivate.d/env_vars.sh

# Add environment variables for activation
echo '#!/bin/sh' >> /etc/pip/activate.d/env_vars.sh
echo 'export OLD_LD_LIBRARY_PATH=${LD_LIBRARY_PATH}' >> /etc/pip/activate.d/env_vars.sh
echo 'export LD_LIBRARY_PATH=/usr/local/lib/:${OLD_LD_LIBRARY_PATH}' >> /etc/pip/activate.d/env_vars.sh

# Add environment variables for deactivation
echo '#!/bin/sh' >> /etc/pip/deactivate.d/env_vars.sh
echo 'export LD_LIBRARY_PATH=${OLD_LD_LIBRARY_PATH}' >> /etc/pip/deactivate.d/env_vars.sh
echo 'unset OLD_LD_LIBRARY_PATH' >> /etc/pip/deactivate.d/env_vars.sh
