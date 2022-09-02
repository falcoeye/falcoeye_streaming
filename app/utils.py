import os
from flask import current_app
import shutil
import string
import random
import logging

def message(status, message):
	response_object = {"status": status, "message": message}
	return response_object


def validation_error(status, errors):
	response_object = {"status": status, "errors": errors}

	return response_object


def err_resp(msg, reason, code):
	err = message(False, msg)
	err["error_reason"] = reason
	return err, code


def internal_err_resp():
	err = message(False, "Something went wrong during the process!")
	err["error_reason"] = "server_error"
	return err, 500

def put(f_from, f_to,app=None):
	

	if app is None:
		app = current_app

	FS_OBJ = app.config["FS_OBJ"]
	f_from = os.path.relpath(f_from)
	f_to = os.path.relpath(f_to)
	
	if app.config["FS_IS_REMOTE"]:
		logging.info(f"Remote put: copying from {f_from} to {f_to}")
		FS_OBJ.put(f_from, f_to)
	else:
		logging.info(f"Local put: copying from {f_from} to {f_to}")
		shutil.copy2(f_from, f_to)


def random_string(N=6):
	randomstr = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))
	logging.info(f"random_string called with N={N}: returning {randomstr}")
	return randomstr

def tempdir():
	import platform
	import tempfile
	tempdir = "/tmp" if platform.system() == "Darwin" else tempfile.gettempdir()
	logging.info(f"tempdir called: return {tempdir}")
	return tempdir

def mkdir(path,app=None):
	path = os.path.relpath(path)
	if app is None:
		app = current_app
	
	FS_OBJ = app.config["FS_OBJ"]
	if FS_OBJ.isdir(path):
		return
	if app.config["FS_IS_REMOTE"]:
		if not path.endswith("/"):
			path = path + "/"
		FS_OBJ.touch(path)
	else:
		FS_OBJ.makedirs(path)

def get_service(service_name,app=None,deployment=None,config=None):

	if deployment:
		_deployment = deployment
		if _deployment == "gcloud" or _deployment == "local":
			return os.environ.get(config.SERVICES[service_name]["env"])
		elif _deployment == "k8s":
			return f"http://" + config.SERVICES[service_name]["k8s"].get_service_address()
	else:
		if app is None:
			app = current_app
		_deployment = app.config["DEPLOYMENT"]
		if _deployment == "gcloud" or _deployment == "local":
			return os.environ.get(app.config["SERVICES"][service_name]["env"])
		elif _deployment == "k8s":
			return f"http://" + app.config["SERVICES"][service_name]["k8s"].get_service_address()
