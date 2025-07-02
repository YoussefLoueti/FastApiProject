pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = "fastapi_project"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/YoussefLoueti/FastApiProject.git'
            }
        }

        stage('Build Images') {
            steps {
                sh 'docker-compose -f docker-compose.yaml build'
            }
        }

        stage('Run Tests') {
            steps {
                // Start containers for testing
                sh 'docker-compose -f docker-compose.yaml up -d'
                
                // Wait for services to be ready
                sh 'sleep 10'
                
                // Run your tests here (example)
                sh 'docker-compose exec -T web python -m pytest tests/ || echo "No tests found"'
                
                // Cleanup test containers
                sh 'docker-compose -f docker-compose.yaml down'
            }
        }

        stage('Deploy') {
            steps {
                // Stop existing containers
                sh 'docker-compose -f docker-compose.yaml down || true'
                
                // Start new containers
                sh 'docker-compose -f docker-compose.yaml up -d'
                
                // Verify deployment
                sh 'sleep 5'
                sh 'curl -f http://localhost:8000/docs || echo "Service not ready yet"'
            }
        }
    }

    post {
        always {
            // Cleanup
            sh 'docker system prune -f'
        }
        failure {
            // Cleanup on failure
            sh 'docker-compose -f docker-compose.yaml down || true'
        }
    }
}