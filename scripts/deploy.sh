#!/bin/bash

set -e

echo "🚀 Deploying AI Production Debugger..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Apply Kubernetes manifests
echo "📦 Creating namespace and RBAC..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml

echo "🔑 Creating secrets..."
kubectl apply -f k8s/secrets.yaml

echo "🔄 Deploying application..."
kubectl apply -f k8s/deployment.yaml

echo "🌐 Setting up ingress..."
kubectl apply -f k8s/ingress.yaml

echo "📊 Setting up HPA (optional)..."
kubectl apply -f k8s/hpa.yaml 2>/dev/null || true

echo "✅ Deployment complete!"
echo ""
echo "📡 Checking status..."
kubectl get all -n ai-debugger

echo ""
echo "🔍 To check logs: kubectl logs -n ai-debugger deployment/ai-debugger"
echo "🌎 To access: http://debugger.your-domain.com (update ingress first!)"
