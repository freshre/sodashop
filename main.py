print("Starting main.py...")
from backend import app
print("App imported successfully")

if __name__ == "__main__":
    import uvicorn
    print("Starting uvicorn...")
    uvicorn.run(app, host="0.0.0.0", port=8000)