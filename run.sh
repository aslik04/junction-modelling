if ! grep -q FLASK_RUN_PORT ".env" 2>/dev/null || ! [[ -d venv ]]; then
    echo Run setup.sh first
    exit 1
fi


app=$1

if [[ -z $app ]]; then
    app=app
fi

# activate the virtual environment for the lab
source venv/bin/activate

# run Flask 
echo Running Flask
# needed python -m flask because flask alone has trouble with spaces in the directory path
FLASK_APP=$app python -m flask run
