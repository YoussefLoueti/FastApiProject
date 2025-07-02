pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = "fastapi_project"
    }

    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/YoussefLoueti/FastApiProject.git'
            }
        }

        stage('Build Images') {
            steps {
                sh 'docker compose -f docker-compose.yaml build'
            }
        }

        stage('Start Containers') {
            steps {
                sh 'docker compose -f docker-compose.yaml up -d'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'echo "TODO: Add test commands here"'
            }
        }

        stage('Cleanup') {
            steps {
                sh 'docker compose -f docker-compose.yaml down'
            }
        }
    }
}
