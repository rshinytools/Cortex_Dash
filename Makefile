# ABOUTME: Makefile for Clinical Dashboard Platform Docker management
# ABOUTME: Provides commands to build, start, stop, restart, and clean Docker containers

.PHONY: help build up down logs test clean dev prod shell-api shell-db restart-all status migrate seed-data health

# Default target
.DEFAULT_GOAL := help

# Colors
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
BLUE   := \033[0;34m
NC     := \033[0m

# Check which docker compose command to use
DOCKER_COMPOSE := $(shell if docker compose version > /dev/null 2>&1; then echo "docker compose"; else echo "docker-compose"; fi)

# Project name for docker compose
PROJECT_NAME := clinical-dashboard

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

restart-all: ## Complete restart: Stop, remove, rebuild, and start all services
	@echo "$(RED)═══════════════════════════════════════════════════════$(NC)"
	@echo "$(YELLOW)🔄 COMPLETE RESTART OF CLINICAL DASHBOARD$(NC)"
	@echo "$(RED)═══════════════════════════════════════════════════════$(NC)"
	@echo ""
	
	@echo "$(YELLOW)1. Stopping all running processes...$(NC)"
	@if [ -f backend/api.pid ] && kill -0 $$(cat backend/api.pid) 2>/dev/null; then \
		kill $$(cat backend/api.pid) 2>/dev/null || true; \
		rm backend/api.pid; \
		echo "   $(GREEN)✓ Stopped host API server$(NC)"; \
	fi
	@if [ -f frontend/frontend.pid ] && kill -0 $$(cat frontend/frontend.pid) 2>/dev/null; then \
		kill $$(cat frontend/frontend.pid) 2>/dev/null || true; \
		rm frontend/frontend.pid; \
		echo "   $(GREEN)✓ Stopped host frontend server$(NC)"; \
	fi
	@echo ""
	
	@echo "$(YELLOW)2. Stopping all containers...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.local.yml down --remove-orphans || true
	@echo "$(GREEN)✓ All containers stopped$(NC)"
	@echo ""
	
	@echo "$(YELLOW)3. Building Docker images...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.local.yml build
	@echo "$(GREEN)✓ Docker images built$(NC)"
	@echo ""
	
	@echo "$(YELLOW)4. Starting all services in Docker...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.local.yml up -d
	@echo "$(GREEN)✓ All services started$(NC)"
	@echo ""
	
	@echo "$(YELLOW)5. Waiting for services to be ready...$(NC)"
	@echo -n "   Waiting for PostgreSQL..."
	@for i in $$(seq 1 30); do \
		if docker exec cortex_dash-postgres-1 pg_isready -U postgres > /dev/null 2>&1; then \
			echo " $(GREEN)✓ Ready$(NC)"; \
			break; \
		fi; \
		echo -n "."; \
		sleep 1; \
	done
	
	@echo -n "   Waiting for Redis..."
	@for i in $$(seq 1 30); do \
		if docker exec cortex_dash-redis-1 redis-cli ping > /dev/null 2>&1; then \
			echo " $(GREEN)✓ Ready$(NC)"; \
			break; \
		fi; \
		echo -n "."; \
		sleep 1; \
	done
	
	@echo -n "   Waiting for Backend API..."
	@for i in $$(seq 1 60); do \
		if curl -s http://localhost:8000/api/v1/utils/health-check/ > /dev/null 2>&1; then \
			echo " $(GREEN)✓ Ready$(NC)"; \
			break; \
		fi; \
		if [ $$i -eq 60 ]; then \
			echo " $(RED)✗ Failed to start$(NC)"; \
			echo "   $(YELLOW)Check logs with: docker logs cortex_dash-backend-1$(NC)"; \
			exit 1; \
		fi; \
		echo -n "."; \
		sleep 2; \
	done
	
	@echo -n "   Waiting for Frontend..."
	@for i in $$(seq 1 60); do \
		if curl -s http://localhost:3000 > /dev/null 2>&1; then \
			echo " $(GREEN)✓ Ready$(NC)"; \
			break; \
		fi; \
		if [ $$i -eq 60 ]; then \
			echo " $(RED)✗ Failed to start$(NC)"; \
			echo "   $(YELLOW)Check logs with: docker logs cortex_dash-frontend-1$(NC)"; \
		fi; \
		echo -n "."; \
		sleep 2; \
	done
	@echo ""
	
	@echo "$(YELLOW)6. Health check results:$(NC)"
	@make health
	@echo ""
	
	@echo "$(GREEN)═══════════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)🎉 CLINICAL DASHBOARD IS UP AND RUNNING!$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(BLUE)📍 Service URLs:$(NC)"
	@echo "   $(GREEN)Frontend:$(NC)    http://localhost:3000"
	@echo "   $(GREEN)API:$(NC)         http://localhost:8000"
	@echo "   $(GREEN)API Docs:$(NC)    http://localhost:8000/docs"
	@echo "   $(GREEN)ReDoc:$(NC)       http://localhost:8000/redoc"
	@echo "   $(GREEN)Adminer:$(NC)     http://localhost:8080"
	@echo "   $(GREEN)Flower:$(NC)      http://localhost:5555"
	@echo ""
	@echo "$(BLUE)🔑 Default credentials:$(NC)"
	@echo "   Email: $(GREEN)admin@sagarmatha.ai$(NC)"
	@echo "   Password: $(GREEN)adadad123$(NC)"
	@echo ""
	@echo "$(YELLOW)💡 Go to $(GREEN)http://localhost:8000/docs$(YELLOW) to test the API$(NC)"
	@echo ""

build: ## Build all Docker images
	@echo "$(YELLOW)Building Docker images...$(NC)"
	@if [ -f backend/Dockerfile ]; then \
		docker build -t clinical-dashboard-backend ./backend; \
		echo "$(GREEN)✓ Backend image built$(NC)"; \
	else \
		echo "$(YELLOW)No backend Dockerfile found, skipping backend build$(NC)"; \
	fi
	@if [ -f frontend/Dockerfile ]; then \
		docker build -t clinical-dashboard-frontend ./frontend; \
		echo "$(GREEN)✓ Frontend image built$(NC)"; \
	else \
		echo "$(YELLOW)No frontend Dockerfile found, skipping frontend build$(NC)"; \
	fi

up: ## Start all services
	@echo "$(GREEN)Starting Clinical Dashboard...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.local.yml up -d
	@echo "$(GREEN)✓ All services started in Docker!$(NC)"
	@echo ""
	@echo "Waiting for services to be ready..."
	@sleep 5
	@make health
	@echo ""
	@echo "Frontend: http://localhost:3000"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Adminer: http://localhost:8080"
	@echo "Flower: http://localhost:5555"

down: ## Stop all services
	@echo "$(YELLOW)Stopping services...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.local.yml down
	@echo "$(GREEN)✓ All services stopped$(NC)"

logs: ## View logs (use: make logs service=backend)
	@if [ -z "$(service)" ]; then \
		echo "$(YELLOW)Showing all logs (use 'make logs service=<name>' for specific service)$(NC)"; \
		$(DOCKER_COMPOSE) -f docker-compose.local.yml logs -f; \
	else \
		$(DOCKER_COMPOSE) -f docker-compose.local.yml logs -f $(service); \
	fi

test: ## Run API tests
	@echo "$(YELLOW)Running API tests...$(NC)"
	@docker exec cortex_dash-backend-1 python test_api.py

clean: ## Remove all containers and volumes (WARNING: Deletes ALL data!)
	@echo "$(RED)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(RED)║                    ⚠️  WARNING ⚠️                            ║$(NC)"
	@echo "$(RED)║                                                            ║$(NC)"
	@echo "$(RED)║  This will permanently delete:                             ║$(NC)"
	@echo "$(RED)║  • All database data                                       ║$(NC)"
	@echo "$(RED)║  • All clinical study data                                 ║$(NC)"
	@echo "$(RED)║  • All user accounts and settings                          ║$(NC)"
	@echo "$(RED)║  • All pipeline configurations                             ║$(NC)"
	@echo "$(RED)║  • All Redis cache data                                    ║$(NC)"
	@echo "$(RED)║  • All Docker images                                       ║$(NC)"
	@echo "$(RED)║                                                            ║$(NC)"
	@echo "$(RED)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@printf "Are you absolutely sure you want to delete everything? [y/N] "; \
	read REPLY; \
	case "$$REPLY" in \
		[yY]) \
			echo "$(YELLOW)Stopping all services...$(NC)"; \
			make down; \
			echo "$(YELLOW)Removing all containers, volumes, and images...$(NC)"; \
			$(DOCKER_COMPOSE) -f docker-compose.local.yml down -v --remove-orphans --rmi local; \
			echo "$(GREEN)✓ All data has been deleted!$(NC)"; \
			;; \
		*) \
			echo "$(GREEN)Cleanup cancelled.$(NC)"; \
			;; \
	esac

dev: ## Start in development mode with hot reload
	@echo "$(GREEN)Starting in development mode...$(NC)"
	@make up
	@echo ""
	@echo "$(GREEN)Development mode started!$(NC)"
	@echo "All services are running in Docker containers with hot reload enabled."
	@echo "API: http://localhost:8000 (with hot reload)"
	@echo "Frontend: http://localhost:3000 (with hot reload)"
	@echo "Flower: http://localhost:5555 (Celery monitoring)"

prod: ## Start in production mode
	@echo "$(GREEN)Starting in production mode...$(NC)"
	@echo "$(YELLOW)Note: For production, use proper deployment with Docker/Kubernetes$(NC)"
	@make up

shell-api: ## Open Python shell with app context
	@docker exec -it cortex_dash-backend-1 python -c "from app.models import *; from app.crud import *; from sqlmodel import Session, create_engine; from app.core.config import settings; engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI)); session = Session(engine); import IPython; IPython.embed()"

shell-db: ## Open PostgreSQL shell
	@docker exec -it cortex_dash-postgres-1 psql -U postgres -d clinical_dashboard

status: ## Check service status
	@echo "$(YELLOW)Service Status:$(NC)"
	@echo ""
	@$(DOCKER_COMPOSE) -f docker-compose.local.yml ps

health: ## Health check for all services
	@echo -n "   PostgreSQL: "
	@if docker exec cortex_dash-postgres-1 pg_isready -U postgres > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Healthy$(NC)"; \
	else \
		echo "$(RED)✗ Unhealthy$(NC)"; \
	fi
	
	@echo -n "   Redis: "
	@if docker exec cortex_dash-redis-1 redis-cli ping > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Healthy$(NC)"; \
	else \
		echo "$(RED)✗ Unhealthy$(NC)"; \
	fi
	
	@echo -n "   API Backend: "
	@if curl -s http://localhost:8000/api/v1/utils/health-check/ > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Healthy$(NC)"; \
	else \
		echo "$(RED)✗ Unhealthy$(NC)"; \
	fi
	
	@echo -n "   Frontend: "
	@if curl -s http://localhost:3000 > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Healthy$(NC)"; \
	else \
		echo "$(RED)✗ Unhealthy$(NC)"; \
	fi

restart: ## Restart all services
	@echo "$(YELLOW)Restarting services...$(NC)"
	@make down
	@sleep 2
	@make up
	@echo "$(GREEN)Services restarted!$(NC)"

migrate: ## Run database migrations
	@echo "$(YELLOW)Running database migrations...$(NC)"
	@docker exec cortex_dash-backend-1 alembic upgrade head
	@echo "$(GREEN)✓ Migrations complete$(NC)"

seed-data: ## Generate test data
	@echo "$(YELLOW)Generating test data...$(NC)"
	@docker exec cortex_dash-backend-1 python test_api.py
	@echo "$(GREEN)✓ Test data created$(NC)"

api-logs: ## View API logs
	@docker logs -f cortex_dash-backend-1

frontend-logs: ## View Frontend logs
	@docker logs -f cortex_dash-frontend-1

celery-logs: ## View Celery worker logs
	@docker logs -f cortex_dash-celery-worker-1

# Code quality commands
format: ## Format code with black and isort
	@echo "$(YELLOW)Formatting backend code...$(NC)"
	@docker exec cortex_dash-backend-1 sh -c "black app && isort app"
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint: ## Run linting checks
	@echo "$(YELLOW)Running linting checks...$(NC)"
	@docker exec cortex_dash-backend-1 sh -c "mypy app && ruff check app && ruff format app --check"
	@echo "$(GREEN)✓ Linting complete$(NC)"

test-backend: ## Run backend tests with pytest
	@echo "$(YELLOW)Running backend tests...$(NC)"
	@docker exec cortex_dash-backend-1 pytest -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-frontend: ## Run frontend tests
	@echo "$(YELLOW)Running frontend tests...$(NC)"
	@docker exec cortex_dash-frontend-1 npm test
	@echo "$(GREEN)✓ Tests complete$(NC)"

build-frontend: ## Build frontend for production
	@echo "$(YELLOW)Building frontend for production...$(NC)"
	@docker exec cortex_dash-frontend-1 npm run build
	@echo "$(GREEN)✓ Frontend build complete$(NC)"

lint-frontend: ## Run frontend linting
	@echo "$(YELLOW)Running frontend linting...$(NC)"
	@docker exec cortex_dash-frontend-1 npm run lint
	@echo "$(GREEN)✓ Linting complete$(NC)"

# Aliases
start: up ## Alias for 'up'
stop: down ## Alias for 'down'
reset: clean restart-all ## Reset everything and start fresh

# Quick commands
quickstart: restart-all seed-data ## Quick start with test data
	@echo "$(GREEN)Quick start complete with test data!$(NC)"

demo: quickstart ## Run demo after quick start
	@echo "$(YELLOW)Opening API documentation...$(NC)"
	@sleep 2
	@python3 -m webbrowser http://localhost:8000/docs 2>/dev/null || echo "Please open http://localhost:8000/docs in your browser"