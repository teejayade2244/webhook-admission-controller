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

