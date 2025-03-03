# backend/server.py

"""

"""

import uvicorn

if __name__ == "__main__":
    # Instead of "app_setup:app", do "backend.app_setup:app" if you run from parent.
    # But if you prefer "app_setup:app" from inside the 'backend' folder, see below.
    uvicorn.run("backend.app_setup:app", host="0.0.0.0", port=8000, reload=False)
