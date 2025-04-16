# Kubernetes Validating Admission Webhook Controller

A custom Kubernetes validating admission webhook that enforces security policies at the API server level. This webhook intercepts pod creation requests and validates them against security best practices before they're persisted to etcd.
![image](https://github.com/user-attachments/assets/e5aaf4b7-fcb5-4ccf-bb08-5e5978acb684)

## 🛡️ Security Policies Enforced

This admission controller enforces the following security policies:

1. **Block Privileged Containers**: Prevents containers from running with privileged security context, reducing the risk of container escapes and host system compromise (aligns with CIS Kubernetes Benchmark)

2. **Namespace Isolation**: Denies pod creation in the `default` namespace, enforcing proper namespace usage for better workload isolation

3. **Resource Limit Requirements**: Ensures all containers specify CPU and memory limits to prevent resource exhaustion attacks and "noisy neighbor" issues

## 🏗️ Architecture
1. The API server receives a request to create/update a Pod
2. The ValidatingWebhookConfiguration routes matching requests to our webhook
3. Our Flask webhook server validates the Pod spec against security policies
4. The webhook returns an AdmissionReview response allowing or denying the request
5. The API server either persists the Pod to etcd or returns an error to the user

## 🚀 Getting Started
### Prerequisites
- Kubernetes cluster v1.16+
- kubectl configured with cluster access
- Python 3.8+
- Docker for building the container image
- OpenSSL for certificate generation

### Installation
#### 1. Clone the Repository
```bash
git clone https://github.com/teejayade2244/webhook-admission-controller.git
cd webhook-admission-controller
```

#### 2. Generate TLS Certificates

```bash
./CA-script.sh
```

This script generates a self-signed TLS certificate and key for secure communication between the API server and webhook.
#### 3. Create a Namespace and TLS Secret

```bash
kubectl create ns webhooks
kubectl -n webhooks create secret tls webhook-tls --cert=tls.crt --key=tls.key
```

#### 4. Build and Push the Docker Image

```bash
docker build -t <your-repo>/validating-webhook-ac:latest .
docker push <your-repo>/validating-webhook-ac:latest
```

#### 5. Deploy the Webhook Server
Update the image name in `kubernetes/deployment.yaml` and apply:

```bash
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/rbac.yaml
```
OR
 ```bash
  ./K8s-script.sh
```

#### 6. Configure the ValidatingWebhookConfiguration

```bash
kubectl apply -f kubernetes/customVWAC.yaml
```

## 🧪 Testing the Webhook

### Test Block Privileged Containers
Try to create a privileged Pod:

```bash
kubectl run nginx --image=nginx --overrides='{"spec":{"containers":[{"name":"nginx","image":"nginx","securityContext":{"privileged":true}}]}}'
```

Expected output:
```
Error from server: admission webhook "pod-policy.security.acme.com" denied the request: Container 'nginx' is privileged which is not allowed
```

### Test Default Namespace Policy
Try to create a Pod in the default namespace:

```bash
kubectl run nginx --image=nginx
```

Expected output:
```
Error from server: admission webhook "pod-policy.security.acme.com" denied the request: Validation failed: Pods cannot be deployed in 'default' namespace
```

### Test Resource Limits Policy

Try to create a Pod without resource limits:

```bash
kubectl -n test-ns run nginx --image=nginx
```

Expected output:
```
Error from server: admission webhook "pod-policy.security.acme.com" denied the request: Container 'nginx' must define CPU and memory limits
```

## 📂 Project Structure

```
webhook-admission-controller/
├── app/
│   ├── __init__.py
│   ├── webhook.py          # Main webhook implementation
├── kubernetes/             # K8s manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── rbac.yaml
│   └── validating-webhook-config.yaml
├── scripts/
│   └── generate-certs.sh   # Certificate generation script
├── Dockerfile
├── Jenkinsfile
├── requirements.txt
└── test_webhook.py         # Unit tests
```

## 🛠️ CI/CD Integration

![image](https://github.com/user-attachments/assets/b8e6cc2b-793e-4a20-ac5e-036df4feac51)

This project includes a Jenkins pipeline for building, testing, and deploying the webhook. The pipeline:
1. Checks out the code from the repository
2. Installs Python dependencies
3. Runs unit tests
4. Builds and pushes the Docker image
5. Deploys the webhook to the Kubernetes cluster
   
![image](https://github.com/user-attachments/assets/02c72c00-2139-4b31-9852-91cf737e3b72)

For detailed pipeline configuration, see the `Jenkinsfile` in the repository.

## 🧩 Customizing Security Policies

To add or modify security policies:

1. Create a new validator in the `app/validators/` directory
2. Import and register it in `app/webhook.py`
3. Add tests in `test_webhook.py`
4. Rebuild and redeploy the webhook

## 📝 License

[MIT License](LICENSE)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📫 Contact
If you have any questions or suggestions, please open an issue or contact me via LinkedIn.

---

⭐ If you find this project useful, please consider giving it a star on GitHub!





