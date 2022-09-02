import os
import requests
from dotenv import load_dotenv

from app import create_app
from config import config_by_name
from app.utils import get_service
import logging 
#from falcoeye_kubernetes import FalcoServingKube

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



config_name = os.getenv("FLASK_CONFIG") or "default"
config = config_by_name[config_name]

URL = get_service("falcoeye-backend",deployment=config.DEPLOYMENT,config=config)
 
payload =  {
        "email": streaming_user.strip(),
        "password": streaming_password.strip()
}
logging.info(f"Logging to backend server on {URL}")
r = requests.post(f"{URL}/auth/login", json=payload)

assert "access_token" in r.json()
access_token = r.json()["access_token"]
logging.info(f"Access token received with size {len(access_token)}")
os.environ["JWT_KEY"] = f'JWT {access_token}'

app = create_app(config_name)
