import json
import logging
import os

import yaml
from kubernetes import client, config, utils

logger = logging.getLogger(__name__)

SERVING_TEMPLATE = os.path.join(
    os.path.dirname(__file__), "resources/tf-serving-template.yml"
)


def skip_if_already_exists(e):
    info = json.loads(e.api_exceptions[0].body)
    if info.get("reason").lower() == "alreadyexists":
        return True
    else:
        logger.debug(e)
        return False


class FalcoServingKube:
    ARTIFACT_REGISTRY = None
    def __init__(
        self,
        name,
        template=None,
        image=None,
        replicas=1,
        port=8501,
        namespace="default",
    ):
        self.name = name
        self.service_name = self.name+"-svc"
        self.base_name = name.split("/")[-1]
        self.template = template
        self.image = image
        self.replicas = replicas
        self.port = port
        self.namespace = namespace

        if not self.name:
            raise RuntimeError("name should not be empty")

        self.template = list(self._get_deployment_template())
        try:
            config.load_kube_config()
        except:
            config.load_incluster_config()

    def _get_deployment_template(self):
        if not self.template:
            with open(SERVING_TEMPLATE) as f:
                template = self._fill_deployment_template(f.read())
                template = yaml.safe_load_all(template)

        elif isinstance(self.template, str):
            with open(self.template) as f:
                template = yaml.safe_load_all(f)

        else:
            raise NotImplementedError(
                f"parsing template of type {type(self.template)} is not implemented yet"
            )

        return template

    def _fill_deployment_template(self, template):
        template = template.replace("$appname", self.name)
        template = template.replace("$replicas", str(self.replicas))
        template = template.replace("$port", str(self.port))
        
        # @jalalirs: create it if None but don't set it (i.e. self.image=...)
        # I don't like setting object attributes inside operation functions
        image = self.image
        if not image:
            image = f"{self.name}:latest"
            if FalcoServingKube.ARTIFACT_REGISTRY:
                image = f"{FalcoServingKube.ARTIFACT_REGISTRY}/{image}"
        
        template = template.replace("$image", image)

        return template

    def start(self):
        k8s_client = client.ApiClient()
        yaml_objects = self.template
        for data in yaml_objects:
            try:
                utils.create_from_dict(
                    k8s_client, data=data, namespace=self.namespace, verbose=True
                )

            except utils.FailToCreateError as e:
                return skip_if_already_exists(e)

        return True

    def delete_deployment(self):
        api = client.AppsV1Api()
        try:
            api.delete_namespaced_deployment(
                name=self.name,
                namespace=self.namespace,
                body=client.V1DeleteOptions(
                    propagation_policy="Foreground", grace_period_seconds=5
                ),
            )
            logger.info(f"deployment `{self.name}` deleted.")
        except client.exceptions.ApiException as e:
            if e.reason == "Not Found":
                logger.debug(f"Deployment {self.name} has been deleted already.")

    def delete_service(self):
        api = client.CoreV1Api()
        try:
            api.delete_namespaced_service(
                name=self.name,
                namespace=self.namespace,
                body=client.V1DeleteOptions(
                    propagation_policy="Foreground", grace_period_seconds=5
                ),
            )
            logger.info(f"deployment `{self.name}` deleted.")
        except client.exceptions.ApiException as e:
            if e.reason == "Not Found":
                logger.debug(f"Deployment {self.name} has been deleted already.")

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
            service = v1.read_namespaced_service(namespace=self.namespace, name=self.service_name)
            if hostname:
                host = service.status.load_balancer.ingress[0].hostname
            else:
                host = service.status.load_balancer.ingress[0].ip
        else:
            host = service.spec.cluster_ip

        return f"{host}:{port}"

    @staticmethod
    def set_artifact_registry(registry):
        if registry[-1] == "/":
            registry = registry[:-1]
        FalcoServingKube.ARTIFACT_REGISTRY = registry

    def scale(self, n):
        pass
