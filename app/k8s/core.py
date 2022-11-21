import json
import logging
import os

import yaml
from kubernetes import client, config, utils
import kubernetes
import time

logger = logging.getLogger(__name__)

SERVING_TEMPLATE = {
    "job":os.path.join(
        os.path.dirname(__file__), "resources/capture-job-template.yml"
    ), 
}


def skip_if_already_exists(e):
    info = json.loads(e.api_exceptions[0].body)
    if info.get("reason").lower() == "alreadyexists":
        return True
    else:
        logger.debug(e)
        return False

class FalcoServingKube:
    def __init__(
        self,
        name,
        namespace="default"
    ):
        self.name = name
        self.service_name = self.name+"-svc"
        self.base_name = name.split("/")[-1]
        self.namespace = namespace
        
        try:
            config.load_kube_config()
        except:
            config.load_incluster_config()

    def deployment_exists(self):
        v1 = client.AppsV1Api()
        resp = v1.list_namespaced_deployment(namespace=self.namespace)
        for i in resp.items:
            if i.metadata.name == self.name:
                return True
        return False

    def service_exists(self):
        v1 = client.CoreV1Api()
        resp = v1.list_namespaced_service(namespace=self.namespace)
        for i in resp.items:
            if i.metadata.name == self.name:
                return True
        return False

    def is_running(self):
        if self.deployment_exists() and self.service_exists():
            return True
        return False

    def get_service_address(self, external=False, hostname=False):
        if not self.is_running():
            logger.error(f"No running deployment found for {self.name}.")
            return None

        v1 = client.CoreV1Api()
        service = v1.read_namespaced_service(namespace=self.namespace, name=self.name)
        [port] = [port.port for port in service.spec.ports]
        
        if external:
            try:
                service = v1.read_namespaced_service(namespace=self.namespace, name=self.service_name)
            except Exception :
                # trying without -svc
                service = v1.read_namespaced_service(namespace=self.namespace, name=self.service_name[:-4])
            if hostname:
                host = service.status.load_balancer.ingress[0].hostname
            else:
                host = service.status.load_balancer.ingress[0].ip
        else:
            host = service.spec.cluster_ip

        return f"{host}:{port}"


class FalcoJobKube:
    def __init__(
        self,
        name,
        job_path,
        namespace="default"
    ):
        self._name = name
        self._job_path = job_path
        self._namespace = namespace
        
        if not self._name:
            raise RuntimeError("name should not be empty")
        self._template = self._get_deployment_template()
   
        try:
            config.load_kube_config()
        except:
            config.load_incluster_config()
    
    def _get_deployment_template(self):
        
        with open(SERVING_TEMPLATE["job"]) as f:
            template = self._fill_deployment_template(f.read())
            template = list(yaml.safe_load_all(template))[0]

        return template

    def _fill_deployment_template(self, template):
        template = template.replace("$jobname", self._name)        
        template = template.replace("$capture_path", self._job_path)
        logging.info(template)
        return template

    def start(self,watch=False):
        
        api_instance = client.BatchV1Api()
        # Create the specification of deployment
        spec = client.V1JobSpec(
            template=self._template, backoff_limit=0)
        # Instantiate the job object
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=self._name),
            spec=spec)
        api_response = api_instance.create_namespaced_job(body=job,namespace="default")
        logging.info("Job created. status='%s'" % str(api_response.status))    
            
        if watch:
            js = api_instance.read_namespaced_job_status(self._name,"default").status
            status = js.succeeded or js.failed
            logging.info(f"SUCCEDED: {js.succeeded} FAILED: {js.failed}")
            while not status:
                time.sleep(1)
                logging.info(f"SUCCEDED: {js.succeeded} SUCCEDED: {js.failed}")
                js = api_instance.read_namespaced_job_status(self._name,"default").status
                status = js.succeeded or js.failed
            return js.succeeded

        return job