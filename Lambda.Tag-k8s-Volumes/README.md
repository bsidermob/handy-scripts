# AWS EC2 tag volumes script

This tags volumes which belong to Kubernetes as this isn't done neither by KOPS nor by
AWS autoscaling groups (ASG). They just don't support this functionality. 

It's supposed to run as a Lambda function on a regular basis. Deploy with deploy.sh
