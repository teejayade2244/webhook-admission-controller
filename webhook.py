from flask import Flask, request, jsonify, Response
import logging
import os
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_response(uid: str, allowed: bool, message: str = None) -> Response:
    """Create properly formatted AdmissionReview response"""
    response = {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "uid": uid,
            "allowed": allowed
        }
    }
    
    if message:
        response["response"]["status"] = {
            "code": 403 if not allowed else 200,
            "message": message
        }
    
    return Response(
        response=json.dumps(response),
        status=200,
        mimetype='application/json'
    )

def validate_resources(container: dict, container_name: str) -> list:
    """Validate that container has resource limits and requests defined"""
    errors = []
    resources = container.get('resources', {})
    
    if not resources:
        errors.append(f"Container '{container_name}': No resources defined")
        return errors
    
    if not resources.get('limits'):
        errors.append(f"Container '{container_name}': No resource limits defined")
    
    if not resources.get('requests'):
        errors.append(f"Container '{container_name}': No resource requests defined")
    
    return errors

@app.route('/validate', methods=['POST'])
def validate():
    if not request.is_json:
        return make_response("", False, "Request must be JSON"), 400

    try:
        admission_review = request.get_json()
        if not admission_review or "request" not in admission_review:
            return make_response("", False, "Invalid AdmissionReview request"), 400

        request_info = admission_review["request"]
        uid = request_info.get("uid", "")
        pod = request_info.get("object", {})
        namespace = request_info.get("namespace", "")
        pod_name = pod.get("metadata", {}).get("name", "unnamed-pod")
        
        logger.info(f"Validating pod {pod_name} in namespace {namespace}")
        errors = []

        # Security Rules
        if namespace == "default":
            errors.append("Pods cannot be deployed in 'default' namespace")
            
        # Container Validation
        for container in pod.get("spec", {}).get("containers", []):
            container_name = container.get('name', 'unnamed-container')
            
            # Check for privileged containers
            if container.get("securityContext", {}).get("privileged", False):
                errors.append(f"Container '{container_name}': privileged mode not allowed")
            
            # Check for resource requirements
            errors.extend(validate_resources(container, container_name))

        if errors:
            message = "Validation failed: " + "; ".join(errors)
            logger.warning(f"Rejected pod {pod_name}: {message}")
            return make_response(uid, False, message)
        
        logger.info(f"Approved pod: {pod_name}")
        return make_response(uid, True)

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", exc_info=True)
        return make_response(
            request.get_json().get("request", {}).get("uid", ""),
            False,
            f"Internal error: {str(e)}"
        )

@app.route('/healthz', methods=['GET'])
def healthz():
    return "ok", 200

if __name__ == '__main__':
    cert_path = os.getenv("TLS_CERT_PATH", "/etc/webhook/certs/tls.crt")
    key_path = os.getenv("TLS_KEY_PATH", "/etc/webhook/certs/tls.key")
    
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        logger.error("TLS certificate or key not found!")
        exit(1)
        
    logger.info("Starting Kubernetes admission controller webhook")
    app.run(
        host='0.0.0.0',
        port=8443,
        ssl_context=(cert_path, key_path),
        debug=False
    )