pipeline {
    agent any

    environment {
        CONFIG_FILE = 'pipeline.config'
        REGISTRY_CREDS = 'dockerhub-credentials'
        DEPLOY_SSH_CREDS = 'deploy-server-ssh'
        DOCKER_REGISTRY = 'registry-1.docker.io'
        VENV_PATH = 'venv'
    }

    stages {
        stage('checkout') {
            steps {
                checkout scm
                script {
                    // Parse pipeline.config (KEY=VALUE format)
                    def configLines = readFile(CONFIG_FILE).readLines()
                    def config = [:]
                    configLines.each { line ->
                        if (line && !line.trim().startsWith('#') && line.contains('=')) {
                            def parts = line.split('=', 2)
                            config[parts[0].trim()] = parts[1].trim()
                        }
                    }
                    env.DOCKER_IMAGE = config.DOCKER_IMAGE
                    env.DEPLOY_HOST = config.DEPLOY_HOST
                    env.DEPLOY_USER = config.DEPLOY_USER
                    env.DEPLOY_BRANCH = config.DEPLOY_BRANCH
                    env.CONTAINER_NAME = config.CONTAINER_NAME
                    
                    echo "✅ Config loaded: ${DOCKER_IMAGE} → ${DEPLOY_HOST}:${CONTAINER_NAME}"
                }
            }
        }

        stage('setup') {
            steps {
                script {
                    echo "📦 Setting up Python environment..."
                    sh '''
                        python3 -m venv ${VENV_PATH}
                        . ${VENV_PATH}/bin/activate
                        pip install --upgrade pip
                        
                        if [ -f requirements.txt ]; then
                            echo "   Installing dependencies..."
                            pip install -r requirements.txt
                        fi
                        
                        # Install flake8 for quality checks (tests disabled)
                        pip install --quiet flake8
                    '''
                }
            }
        }

        stage('build') {
            steps {
                script {
                    echo "🔨 Building Docker image..."
                    sh "docker build -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER} -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:latest ."
                    echo "✅ Built: ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER}"
                }
            }
        }

        stage('quality') {
            steps {
                script {
                    echo "🔍 Running flake8 quality checks..."
                    sh '''
                        . ${VENV_PATH}/bin/activate
                        
                        # Critical errors: FAIL the build
                        echo "   [1/2] Checking critical errors (E9,F63,F7,F82)..."
                        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics \
                            --exclude=${VENV_PATH},.git,__pycache__,.pytest_cache
                        
                        # Style warnings: report only, don't fail
                        echo "   [2/2] Checking style guidelines..."
                        flake8 . --count --exit-zero \
                            --max-complexity=10 \
                            --max-line-length=127 \
                            --statistics \
                            --exclude=${VENV_PATH},.git,__pycache__,.pytest_cache
                    '''
                    echo "✅ Quality checks passed"
                }
            }
        }

        stage('test') {
            steps {
                script {
                    // Tests disabled per config - keep stage for pipeline structure
                    echo "🧪 Test stage: Tests disabled in configuration, skipping execution"
                    sh 'echo "⏭️ No test suite configured - stage kept for pipeline consistency"'
                }
            }
        }

        stage('deploy') {
            when {
                branch "${env.DEPLOY_BRANCH}"
            }
            steps {
                script {
                    echo "🚀 Deploying to ${DEPLOY_HOST}..."
                    
                    // Push Docker image to registry
                    withCredentials([usernamePassword(
                        credentialsId: REGISTRY_CREDS,
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        echo "   Logging into Docker registry..."
                        sh "echo ${DOCKER_PASS} | docker login ${DOCKER_REGISTRY} -u ${DOCKER_USER} --password-stdin"
                        
                        echo "   Pushing ${DOCKER_IMAGE}:${BUILD_NUMBER}..."
                        sh "docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER}"
                        
                        echo "   Pushing ${DOCKER_IMAGE}:latest..."
                        sh "docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:latest"
                        
                        sh "docker logout ${DOCKER_REGISTRY}"
                    }

                    // Deploy to laptop via SSH
                    echo "   Deploying via SSH to ${DEPLOY_USER}@${DEPLOY_HOST}..."
                    sshagent(credentials: [DEPLOY_SSH_CREDS]) {
                        sh """
                            ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 ${DEPLOY_USER}@${DEPLOY_HOST} \\
                                "echo '${DOCKER_PASS}' | docker login ${DOCKER_REGISTRY} -u '${DOCKER_USER}' --password-stdin && \\
                                echo '   Pulling image...' && \\
                                docker pull ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER} && \\
                                echo '   Stopping old container...' && \\
                                docker stop ${CONTAINER_NAME} 2>/dev/null || true && \\
                                echo '   Removing old container...' && \\
                                docker rm ${CONTAINER_NAME} 2>/dev/null || true && \\
                                echo '   Starting new container...' && \\
                                docker run -d --name ${CONTAINER_NAME} --restart=unless-stopped ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER} && \\
                                echo '   Cleaning up...' && \\
                                docker image prune -f && \\
                                docker logout ${DOCKER_REGISTRY} && \\
                                echo '✅ ${CONTAINER_NAME} is running'"
                        """
                    }
                    echo "✅ Deployment complete"
                }
            }
        }
    }

    post {
        always {
            // Cleanup local artifacts
            sh 'docker rmi ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER} 2>/dev/null || true'
            sh 'docker rmi ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:latest 2>/dev/null || true'
            cleanWs()
        }
        failure {
            echo '❌ Pipeline FAILED - Check console output'
        }
        success {
            echo "🎉 SUCCESS: ${DOCKER_IMAGE}:${BUILD_NUMBER} deployed to ${DEPLOY_HOST}"
        }
    }
}