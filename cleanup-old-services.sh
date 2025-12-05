#!/bin/bash

# Cleanup script to remove old/unused services from Kubernetes

set -e

echo "Cleaning up old services from restaurant-system namespace..."

# Delete old services that are failing
kubectl delete deployment api-gateway -n restaurant-system --ignore-not-found=true
kubectl delete deployment kitchen-service -n restaurant-system --ignore-not-found=true
kubectl delete deployment order-service -n restaurant-system --ignore-not-found=true

# Delete old services
kubectl delete service api-gateway -n restaurant-system --ignore-not-found=true
kubectl delete service kitchen-service -n restaurant-system --ignore-not-found=true
kubectl delete service order-service -n restaurant-system --ignore-not-found=true

# Delete RabbitMQ if not needed (we're only using auth and restaurant services)
kubectl delete statefulset rabbitmq -n restaurant-system --ignore-not-found=true
kubectl delete service rabbitmq -n restaurant-system --ignore-not-found=true

echo "Cleanup complete!"
echo ""
echo "Remaining pods:"
kubectl get pods -n restaurant-system
