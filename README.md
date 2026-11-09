# healthcare-cloud-monitoring-system
Cloud-based Healthcare Application Deployment and Health Monitoring System with Automated CI/CD, SLA Monitoring, Docker and AWS.

## CI/CD Pipeline

This project uses GitHub Actions to automate application deployment.

Deployment workflow:

1. Developer pushes code to the main branch.
2. GitHub Actions validates Python syntax.
3. AWS credentials are securely loaded from GitHub Secrets.
4. AWS Systems Manager sends deployment commands to EC2.
5. EC2 pulls the latest source code.
6. Docker Compose rebuilds and deploys the Flask application.
7. The application health endpoint is checked.

Technologies:
- GitHub Actions
- AWS IAM
- AWS Systems Manager (SSM)
- Amazon EC2
- Docker and Docker Compose
- Flask and Gunicorn
