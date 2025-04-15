# This script generates a new CA and TLS certificates for the webhook server.
openssl genrsa -out ca.key 2048

openssl req -new -x509 -key ca.key -out ca.crt -subj "/CN=Webhook CA"

openssl genrsa -out tls.key 2048
# Create a configuration file for the server certificate
# This file contains the subject alternative names (SANs) for the certificate
# The SANs are used to validate the hostname of the webhook server
# The configuration file is used to generate the certificate signing request (CSR)
# The CSR is then signed by the CA to create the server certificate
# The server certificate is used to secure the connection between the Kubernetes API server and the webhook server and validate the identity of the webhook server
# The server certificate is used to encrypt the communication between the Kubernetes API server and the webhook server

cat > server.conf << EOF
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name

[req_distinguished_name]

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = webhook-service
DNS.2 = webhook-service.webhooks
DNS.3 = webhook-service.webhooks.svc
DNS.4 = webhook-service.webhooks.svc.cluster.local
EOF

# Generate the TLS certificate signing request (CSR)
openssl req -new -key tls.key -out server.csr -subj "/CN=webhook-service.webhooks.svc" -config server.conf
# Sign the certificate with the CA
# The CA creates a serial number file if it doesn't exist
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out tls.crt -extensions v3_req -extfile server.conf

# Create the new secret
sudo kubectl -n webhooks create secret tls webhook-tls --cert=tls.crt --key=tls.key

# Deploy the webhook server
sudo kubectl create -f deployment.yaml  # webhook deployment file

# Wait for the pods to be fully ready
echo "Waiting for webhook pods to be ready..."
sleep 10
sudo kubectl get pods -n webhooks

# Only now apply the webhook configuration with the new CA bundle
CA_BUNDLE=$(cat ca.crt | base64 | tr -d '\n')

# Update the webhook configuration with the new CA bundle
cat > updated-webhook-config.yaml << EOF
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: pod-validation-webhook
webhooks:
- name: webhook-service.webhooks.svc.cluster.local
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE", "UPDATE"]
    resources: ["pods"]
  clientConfig:
    service:
      name: webhook-service
      namespace: webhooks
      path: "/validate"
      port: 8443
    caBundle: ${CA_BUNDLE}
  admissionReviewVersions: ["v1"]
  failurePolicy: Fail
  sideEffects: None
  namespaceSelector:
    matchExpressions:
    - key: kubernetes.io/metadata.name
      operator: NotIn
      values: ["webhooks"]
EOF
# Apply the updated webhook configuration
# This will register the webhook with the new CA bundl
sudo kubectl create -f updated-webhook-config.yaml