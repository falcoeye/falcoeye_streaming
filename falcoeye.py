import os
import requests
from dotenv import load_dotenv

from app import create_app

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# login to backend
streaming_user = os.getenv("STREAMING_USER")
streaming_password = os.getenv("STREAMING_PASSWORD")
URL = os.environ.get("BACKEND_SERVER_NAME", "http://10.101.236.144:5000")
 
payload =  {
        "email": streaming_user.strip(),
        "password": streaming_password.strip()
}
r = requests.post(f"{URL}/auth/login", json=payload)
assert "access_token" in r.json()
access_token = r.json()["access_token"]
os.environ["JWT_KEY"] = access_token

app = create_app(os.getenv("FLASK_CONFIG") or "default")
