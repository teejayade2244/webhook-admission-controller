import unittest
import json
from webhook.webhook import app, validate_resources

class TestWebhook(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
    def test_healthz_endpoint(self):
        """Test health check endpoint"""
        response = self.app.get('/healthz')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), 'ok')

    def test_validate_resources_missing_all(self):
        """Test container with no resources defined"""
        container = {"name": "test-container"}
        errors = validate_resources(container, "test-container")
        self.assertEqual(len(errors), 1)
        self.assertIn("No resources defined", errors[0])

    def test_validate_resources_missing_limits(self):
        """Test container with missing resource limits"""
        container = {
            "name": "test-container",
            "resources": {
                "requests": {
                    "cpu": "100m",
                    "memory": "128Mi"
                }
            }
        }
        errors = validate_resources(container, "test-container")
        self.assertEqual(len(errors), 1)
        self.assertIn("No resource limits defined", errors[0])

    def test_validate_pod_in_default_namespace(self):
        """Test pod deployment in default namespace"""
        data = {
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "request": {
                "uid": "test-uid",
                "namespace": "default",
                "object": {
                    "metadata": {
                        "name": "test-pod"
                    }
                }
            }
        }
        response = self.app.post(
            '/validate',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["response"]["allowed"])
        self.assertIn(
            "Pods cannot be deployed in 'default' namespace",
            response_data["response"]["status"]["message"]
        )

    def test_validate_privileged_container(self):
        """Test pod with privileged container"""
        data = {
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "request": {
                "uid": "test-uid",
                "namespace": "test",
                "object": {
                    "metadata": {
                        "name": "test-pod"
                    },
                    "spec": {
                        "containers": [{
                            "name": "test-container",
                            "securityContext": {
                                "privileged": True
                            }
                        }]
                    }
                }
            }
        }
        response = self.app.post(
            '/validate',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["response"]["allowed"])
        self.assertIn("privileged mode not allowed", response_data["response"]["status"]["message"])

    def test_valid_pod(self):
        """Test valid pod configuration"""
        data = {
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "request": {
                "uid": "test-uid",
                "namespace": "test",
                "object": {
                    "metadata": {
                        "name": "test-pod"
                    },
                    "spec": {
                        "containers": [{
                            "name": "test-container",
                            "resources": {
                                "limits": {
                                    "cpu": "200m",
                                    "memory": "256Mi"
                                },
                                "requests": {
                                    "cpu": "100m",
                                    "memory": "128Mi"
                                }
                            }
                        }]
                    }
                }
            }
        }
        response = self.app.post(
            '/validate',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertTrue(response_data["response"]["allowed"])

if __name__ == '__main__':
    unittest.main()