"""
Entry point for Excelo Financial Backend Application (FastAPI REST Server)
"""
import os
import sys

# Ensure backend modules import correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    print("Starting Excelo Financial Backend API Server on http://127.0.0.1:8000 ...")
    uvicorn.run("backend.api.main:app", host="127.0.0.1", port=8000, reload=True)
