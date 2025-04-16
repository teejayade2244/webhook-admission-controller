# Create the new secret
sudo kubectl -n webhooks create secret tls webhook-tls --cert=tls.crt --key=tls.key

# Create the RBAC configuration
sudo kubectl create -f RBAC.yaml 

# Deploy the webhook service
sudo kubectl create -f service.yaml 

# Deploy the webhook server
sudo kubectl create -f deployment.yaml  # webhook deployment file

# Wait for the pods to be fully ready
echo "Waiting for webhook pods to be ready..."
sleep 10
sudo kubectl get pods -n webhooks

# Only now apply the webhook configuration with the new CA bundle
CA_BUNDLE=$(cat ca.crt | base64 | tr -d '\n')

# Update the webhook configuration with the new CA bundle
cat >> customVWAC.yaml << EOF
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
sudo kubectl create -f customVWAC.yaml.yaml