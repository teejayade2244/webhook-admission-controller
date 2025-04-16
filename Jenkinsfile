pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "teejay4125/validating-webhook-ac:${BUILD_NUMBER}"
    }

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scmGit(
                    branches: [[name: '*/master']],
                    extensions: [],
                    userRemoteConfigs: [[
                        url: 'https://github.com/teejayade2244/webhook-admission-controller.git'
                    ]]
                )
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Unit Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -m pytest test_webhook.py -v
                '''
            }
        }

        stage('Build  Docker Image') {
            steps {
                script {
                    withDockerRegistry(credentialsId: 'docker-credentials') {
                        sh """
                            sudo docker build -t ${DOCKER_IMAGE} .
                        """
                    }
                }
            }
        }

        stage('Trivy Image Scan') {
            steps {
                sh '''
                    echo "Scanning Docker image for vulnerabilities..."
                    trivy image --exit-code 1 --severity CRITICAL,HIGH ${DOCKER_IMAGE}
                '''
            }
        
        }

         stage('Push Docker Image') {
            steps {
                script {
                    withDockerRegistry(credentialsId: 'docker-credentials') {
                        sh """
                            sudo docker push ${DOCKER_IMAGE}
                        """
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                dir("kubernetes/") {
                    withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        sh """
                            ls -l
                            chmod +x k8s-script.sh CA-script.sh
                            ./CA-script.sh
                            ./K8s-script.sh
                        """
                    }
                }
            }
        }


        stage('clean workspace') {
            steps {
                script {
                    echo "Cleaning workspace.."
                    deleteDir()
                }
            }
        }

    }

    post {
        failure {
            echo '🚨 Pipeline failed!'
        }
        success {
            echo '✅ Deployment Successful!'
        }
    }
}
