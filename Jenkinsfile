pipeline {
    agent {
        label 'dev'
    }

    environment {
        LLM_API_KEY     = credentials('GroQ_Secret')
        DEPLOYMENT_NAME = 'backend'
        NAMESPACE       = 'production'
    }

    stages {
        stage('Deploy & Verify Kubernetes') {
            steps {
                withCredentials([file(credentialsId: 'k8s_creds', variable: 'KUBECONFIG')]) {
                    script {
                        sh "kubectl --kubeconfig=${KUBECONFIG} apply -f k8s/ -n ${NAMESPACE}"
                        try {
                            sh """
                              kubectl --kubeconfig=${KUBECONFIG} rollout status deployment/${DEPLOYMENT_NAME} \
                                -n ${NAMESPACE} --timeout=90s
                            """
                            echo "Deployment succeeded!"
                        } catch (Exception e) {
                            echo "Deployment failed or timed out. Triggering AI Diagnostics..."
                            sh """
                              python -m pip install -r requirements.txt
                              python src/main.py \
                                --deployment ${DEPLOYMENT_NAME} \
                                --namespace ${NAMESPACE} \
                                --auto-fix true
                            """
                            error("Deployment failed. Root cause analysis generated above.")
                        }
                    }
                }
            }
        }
    }
}