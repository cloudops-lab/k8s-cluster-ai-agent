pipeline {
    agent {
        label 'dev'
    }

    environment {
        LLM_API_KEY     = credentials('GroQ_Secret')
        KUBECONFIG      = credentials('k8s_creds')      // Added: Binds your Jenkins Secret File
        DEPLOYMENT_NAME = 'backend'
        NAMESPACE       = 'production'
    }

    stages {
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    sh "kubectl --kubeconfig=${KUBECONFIG} apply -f k8s/ -n ${NAMESPACE}"
                }
            }
        }

        stage('Verify Deployment Health') {
            steps {
                script {
                    try {
                        // Waits up to 90 seconds for pods to become ready
                        sh """
                          kubectl --kubeconfig=${KUBECONFIG} rollout status deployment/${DEPLOYMENT_NAME} \
                            -n ${NAMESPACE} --timeout=90s
                        """
                        echo "Deployment succeeded!"
                    } catch (Exception e) {
                        echo "Deployment failed or timed out. Triggering AI Diagnostics..."
                        sh """
                          pip install -r requirements.txt
                          python src/main.py \
                            --deployment ${DEPLOYMENT_NAME} \
                            --namespace ${NAMESPACE} \
                            --auto-fix true
                        """
                        // Explicitly fail the build after analysis and fix
                        error("Deployment failed. Root cause analysis generated above.")
                    }
                }
            }
        }
    }
}