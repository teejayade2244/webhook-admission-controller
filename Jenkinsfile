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

        stage('Build and Push Docker Image') {
            steps {
                script {
                    withDockerRegistry(credentialsId: 'docker-credentials') {
                        sh """
                            sudo docker build -t ${DOCKER_IMAGE} .
                            sudo docker push ${DOCKER_IMAGE}
                        """
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                dir("webhook-admission-controller/kubernetes") {
                    withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        sh """
                            chmod +x k8s-script.sh
                            export KUBECONFIG=${KUBECONFIG}
                            ./k8s-script.sh
                        """
                    }
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
