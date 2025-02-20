#!/bin/bash

portnum=6000  # Fixed port number

if [ "$1" = "--port" ]; then
  portnum="$2"
fi

# Add the FLASK RUN PORT to .env if it doesn't already exist
if ! grep -q FLASK_RUN_PORT ".env" 2>/dev/null; then
    echo "Creating .env"
    echo "FLASK_DEBUG=True" > .env
    echo "FLASK_RUN_PORT=$portnum" >> .env
fi

# Add virtual environment if it doesn't already exist
if ! [[ -d venv ]]; then
    echo "Adding virtual environment"
    python3 -m venv venv

    # Create pip.conf if it doesn't exist
    echo "Creating venv/pip.conf"
    cat <<'EOF' > venv/pip.conf
[install]
user = false
EOF

    source venv/bin/activate

    echo "Setting up Flask requirements"
    # Needed python -m pip because pip alone has trouble with spaces in the directory path
    python -m pip install -r requirements.txt
    deactivate
fi

# Activate the virtual environment for the lab
source venv/bin/activate

# Run Flask
./run.sh app
