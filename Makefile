.PHONY: help build load deploy restart all clean health logs

# Configuration
KIND_CLUSTER := restaurant-cluster
NAMESPACE := restaurant-system

# Colors
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
BLUE   := $(shell tput -Txterm setaf 4)
RESET  := $(shell tput -Txterm sgr0)

help: ## Show this help message
	@echo '$(BLUE)Restaurant Management System - Build & Deploy Commands$(RESET)'
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} { \
		if (/^[a-zA-Z_-]+:.*?##.*$$/) {printf "  ${YELLOW}%-20s${RESET} %s\n", $$1, $$2} \
		else if (/^## .*$$/) {printf "  ${BLUE}%s${RESET}\n", substr($$1,4)} \
		}' $(MAKEFILE_LIST)

## Building

build: ## Build all Docker images
	@echo "$(BLUE)Building all Docker images...$(RESET)"
	docker build -f frontend/Dockerfile -t restaurant-frontend:latest .
	docker tag restaurant-frontend:latest frontend:latest
	docker build -f services/api-gateway/Dockerfile -t api-gateway:latest .
	docker build -f services/auth-service/Dockerfile -t auth-service:latest .
	docker build -f services/restaurant-service/Dockerfile -t restaurant-service:latest .
	docker build -f services/order-service/Dockerfile -t order-service:latest .
	@echo "$(GREEN)✓ All images built!$(RESET)"

build-frontend: ## Build only frontend image
	docker build -f frontend/Dockerfile -t restaurant-frontend:latest .
	docker tag restaurant-frontend:latest frontend:latest

build-api-gateway: ## Build only API gateway image
	docker build -f services/api-gateway/Dockerfile -t api-gateway:latest .

build-auth: ## Build only auth service image
	docker build -f services/auth-service/Dockerfile -t auth-service:latest .

build-restaurant: ## Build only restaurant service image
	docker build -f services/restaurant-service/Dockerfile -t restaurant-service:latest .

build-order: ## Build only order service image
	docker build -f services/order-service/Dockerfile -t order-service:latest .

## Loading into KIND

load: ## Load all images into KIND cluster
	@echo "$(BLUE)Loading images into KIND...$(RESET)"
	kind load docker-image restaurant-frontend:latest --name $(KIND_CLUSTER)
	kind load docker-image frontend:latest --name $(KIND_CLUSTER)
	kind load docker-image api-gateway:latest --name $(KIND_CLUSTER)
	kind load docker-image auth-service:latest --name $(KIND_CLUSTER)
	kind load docker-image restaurant-service:latest --name $(KIND_CLUSTER)
	kind load docker-image order-service:latest --name $(KIND_CLUSTER)
	@echo "$(GREEN)✓ All images loaded!$(RESET)"

load-frontend: ## Load only frontend image
	kind load docker-image restaurant-frontend:latest --name $(KIND_CLUSTER)
	kind load docker-image frontend:latest --name $(KIND_CLUSTER)

load-api-gateway: ## Load only API gateway image
	kind load docker-image api-gateway:latest --name $(KIND_CLUSTER)

load-auth: ## Load only auth service image
	kind load docker-image auth-service:latest --name $(KIND_CLUSTER)

load-restaurant: ## Load only restaurant service image
	kind load docker-image restaurant-service:latest --name $(KIND_CLUSTER)

load-order: ## Load only order service image
	kind load docker-image order-service:latest --name $(KIND_CLUSTER)

## Deployment

restart: ## Restart all deployments
	@echo "$(BLUE)Restarting all deployments...$(RESET)"
	kubectl rollout restart deployment/frontend -n $(NAMESPACE)
	kubectl rollout restart deployment/api-gateway -n $(NAMESPACE)
	kubectl rollout restart deployment/auth-service -n $(NAMESPACE)
	kubectl rollout restart deployment/restaurant-service -n $(NAMESPACE)
	kubectl rollout restart deployment/order-service -n $(NAMESPACE)
	@echo "$(GREEN)✓ All deployments restarted!$(RESET)"

restart-frontend: ## Restart only frontend
	kubectl rollout restart deployment/frontend -n $(NAMESPACE)

restart-api-gateway: ## Restart only API gateway
	kubectl rollout restart deployment/api-gateway -n $(NAMESPACE)

restart-auth: ## Restart only auth service
	kubectl rollout restart deployment/auth-service -n $(NAMESPACE)

restart-restaurant: ## Restart only restaurant service
	kubectl rollout restart deployment/restaurant-service -n $(NAMESPACE)

restart-order: ## Restart only order service
	kubectl rollout restart deployment/order-service -n $(NAMESPACE)

deploy: ## Deploy all Kubernetes resources
	kubectl apply -f infrastructure/kubernetes/postgres-deployment.yaml -n $(NAMESPACE)
	kubectl apply -f infrastructure/kubernetes/redis-deployment.yaml -n $(NAMESPACE)
	kubectl apply -f infrastructure/kubernetes/rabbitmq-deployment.yaml -n $(NAMESPACE)
	kubectl apply -f infrastructure/kubernetes/auth-service-deployment.yaml -n $(NAMESPACE)
	kubectl apply -f infrastructure/kubernetes/restaurant-service-deployment.yaml -n $(NAMESPACE)
	kubectl apply -f infrastructure/kubernetes/order-service-deployment.yaml -n $(NAMESPACE)
	kubectl apply -f infrastructure/kubernetes/api-gateway-deployment.yaml -n $(NAMESPACE)
	kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml -n $(NAMESPACE)
	kubectl apply -f infrastructure/kubernetes/ingress.yaml -n $(NAMESPACE)

## Complete workflows

all: build load restart wait health ## Build, load, restart, and verify (complete pipeline)
	@echo "$(GREEN)✓ Complete deployment finished!$(RESET)"

quick-frontend: build-frontend load-frontend restart-frontend ## Quick update for frontend only
	@echo "$(GREEN)✓ Frontend updated!$(RESET)"

quick-auth: build-auth load-auth restart-auth ## Quick update for auth service only
	@echo "$(GREEN)✓ Auth service updated!$(RESET)"

quick-restaurant: build-restaurant load-restaurant restart-restaurant ## Quick update for restaurant service only
	@echo "$(GREEN)✓ Restaurant service updated!$(RESET)"

quick-order: build-order load-order restart-order ## Quick update for order service only
	@echo "$(GREEN)✓ Order service updated!$(RESET)"

## Monitoring

wait: ## Wait for all rollouts to complete
	@echo "$(BLUE)Waiting for rollouts...$(RESET)"
	kubectl rollout status deployment/frontend -n $(NAMESPACE) --timeout=300s
	kubectl rollout status deployment/api-gateway -n $(NAMESPACE) --timeout=300s
	kubectl rollout status deployment/auth-service -n $(NAMESPACE) --timeout=300s
	kubectl rollout status deployment/restaurant-service -n $(NAMESPACE) --timeout=300s
	kubectl rollout status deployment/order-service -n $(NAMESPACE) --timeout=300s
	@echo "$(GREEN)✓ All rollouts complete!$(RESET)"

status: ## Show status of all resources
	@echo "$(BLUE)=== Pods ===$(RESET)"
	kubectl get pods -n $(NAMESPACE)
	@echo ""
	@echo "$(BLUE)=== Services ===$(RESET)"
	kubectl get svc -n $(NAMESPACE)
	@echo ""
	@echo "$(BLUE)=== Ingress ===$(RESET)"
	kubectl get ingress -n $(NAMESPACE)

health: ## Run health checks on all services
	@echo "$(BLUE)Running health checks...$(RESET)"
	@./scripts/health-check.sh || true

logs: ## Show logs for all services
	@echo "$(YELLOW)Select service:$(RESET)"
	@echo "  1) Frontend"
	@echo "  2) API Gateway"
	@echo "  3) Auth Service"
	@echo "  4) Restaurant Service"
	@echo "  5) Order Service"
	@echo "  6) PostgreSQL"
	@read -p "Enter choice: " choice; \
	case $$choice in \
		1) kubectl logs -f deployment/frontend -n $(NAMESPACE) ;; \
		2) kubectl logs -f deployment/api-gateway -n $(NAMESPACE) ;; \
		3) kubectl logs -f deployment/auth-service -n $(NAMESPACE) ;; \
		4) kubectl logs -f deployment/restaurant-service -n $(NAMESPACE) ;; \
		5) kubectl logs -f deployment/order-service -n $(NAMESPACE) ;; \
		6) kubectl logs -f postgres-0 -n $(NAMESPACE) ;; \
		*) echo "Invalid choice" ;; \
	esac

logs-frontend: ## Show frontend logs
	kubectl logs -f deployment/frontend -n $(NAMESPACE)

logs-api-gateway: ## Show API gateway logs
	kubectl logs -f deployment/api-gateway -n $(NAMESPACE)

logs-auth: ## Show auth service logs
	kubectl logs -f deployment/auth-service -n $(NAMESPACE)

logs-restaurant: ## Show restaurant service logs
	kubectl logs -f deployment/restaurant-service -n $(NAMESPACE)

logs-order: ## Show order service logs
	kubectl logs -f deployment/order-service -n $(NAMESPACE)

## Cleanup

clean: ## Delete all pods (will be recreated)
	kubectl delete pods --all -n $(NAMESPACE)

clean-images: ## Remove all local Docker images
	docker rmi restaurant-frontend:latest frontend:latest api-gateway:latest auth-service:latest restaurant-service:latest order-service:latest || true

## Port forwarding

port-forward: ## Start all port forwards
	@echo "$(BLUE)Starting port forwards...$(RESET)"
	kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80 &
	kubectl port-forward svc/argocd-server -n argocd 8081:443 &
	@echo "$(GREEN)✓ Port forwards started!$(RESET)"
	@echo ""
	@echo "Access URLs:"
	@echo "  Frontend:  http://restaurant.local:8080"
	@echo "  ArgoCD:    https://localhost:8081"
