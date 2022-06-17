import os
import requests
from dotenv import load_dotenv

from app import create_app
import logging 
from falcoeye_kubernetes import FalcoServingKube

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# login to backend
streaming_user = os.getenv("STREAMING_USER")
streaming_password = os.getenv("STREAMING_PASSWORD")

backend_kube = FalcoServingKube("falcoeye-backend")
backend_server = backend_kube.get_service_address()
URL = f"http://{backend_server}"
 
payload =  {
        "email": streaming_user.strip(),
        "password": streaming_password.strip()
}
r = requests.post(f"{URL}/auth/login", json=payload)
assert "access_token" in r.json()
access_token = r.json()["access_token"]
os.environ["JWT_KEY"] = access_token

app = create_app(os.getenv("FLASK_CONFIG") or "default")
