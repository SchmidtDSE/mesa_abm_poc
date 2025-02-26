#/bin/bash

# Note: this script will NOT run in the dev container since docker is not installed in the dev container!
# It is included here for reference - this will need to be run on your local machine. As such, it is not executable.

PROJECT_ID="dse-nps"
CLUSTER_NAME="mesa-gke"
REGION="us-west1"
NETWORK_NAME="mesa-vpc"
SUBNET_NAME="mesa-subnet"
MACHINE_TYPE="e2-standard-4"  # 4 vCPU, 16GB RAM

# Create VPC network
gcloud compute networks create $NETWORK_NAME \
    --project=$PROJECT_ID \
    --subnet-mode=custom

# Create subnet
gcloud compute networks subnets create $SUBNET_NAME \
    --project=$PROJECT_ID \
    --network=$NETWORK_NAME \
    --region=$REGION \
    --range=10.0.0.0/20

# Add firewall rules for GKE
gcloud compute firewall-rules create allow-gke \
  --network=$NETWORK_NAME \
  --allow tcp:443,tcp:10250,tcp:15017 \
  --source-ranges=10.0.0.0/20 \
  --target-tags=gke-${CLUSTER_NAME}

# Create GKE cluster w/ reasonable defaults
gcloud container clusters create $CLUSTER_NAME \
  --project=$PROJECT_ID \
  --region=$REGION \
  --machine-type=$MACHINE_TYPE \
  --network=$NETWORK_NAME \
  --subnetwork=$SUBNET_NAME \
  --num-nodes=1 \
  --min-nodes=1 \
  --max-nodes=4 \
  --enable-autoscaling \
  --monitoring=NONE

# Get credentials
gcloud container clusters get-credentials $CLUSTER_NAME \
  --region=$REGION \
  --project=$PROJECT_ID

# Deploy job
kubectl apply -f sim_job.yml

# Monitor (optional)
kubectl get pods