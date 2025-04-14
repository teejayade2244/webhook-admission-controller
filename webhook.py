from flask import Flask, request, jsonify
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/validate', methods=['POST'])
def validate():
    try:
        admission_review = request.json
        request_info = admission_review["request"]
        pod = request_info["object"]
        namespace = request_info["namespace"]
        pod_name = pod.get("metadata", {}).get("name", "unnamed-pod")
        
        logger.info(f"Validating pod {pod_name} in namespace {namespace}")
        errors = []

        # Security Rule 1: Block default namespace
        if namespace == "default":
            errors.append("Pods cannot be deployed in the 'default' namespace (security policy).")

        # Security Rule 2: Block privileged containers
        for container in pod.get("spec", {}).get("containers", []):
            if container.get("securityContext", {}).get("privileged"):
                errors.append(f"Container '{container['name']}' cannot run in privileged mode (CIS compliance).")

        if errors:
            message = "Validation failed: " + "; ".join(errors)
            logger.warning(f"Rejected pod {pod_name}: {message}")
            return jsonify({
                "response": {
                    "allowed": False,
                    "uid": request_info["uid"],
                    "status": {"message": message}
                }
            })

        logger.info(f"Approved pod: {pod_name}")
        return jsonify({
            "response": {
                "allowed": True,
                "uid": request_info["uid"]
            }
        })

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({
            "response": {
                "allowed": False,
                "status": {"message": f"Internal error: {str(e)}"}
            }
        }), 500

if __name__ == '__main__':
    cert_path = os.getenv("TLS_CERT_PATH", "/etc/webhook/certs/tls.crt")
    key_path = os.getenv("TLS_KEY_PATH", "/etc/webhook/certs/tls.key")
    
    logger.info("Starting Kubernetes admission controller webhook")
    app.run(
        host='0.0.0.0',
        port=8443,  # Standard port for webhooks
        ssl_context=(cert_path, key_path),
        debug=False  # Disable in production!
    )