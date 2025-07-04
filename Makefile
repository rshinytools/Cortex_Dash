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
	
	@echo "$(YELLOW)1. Stopping all containers...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.local.yml down --remove-orphans || true
	@docker stop clinical-postgres clinical-redis clinical-backend clinical-celery-worker clinical-celery-beat 2>/dev/null || true
	@echo "$(GREEN)✓ All containers stopped$(NC)"
	@echo ""
	
	@echo "$(YELLOW)2. Removing all containers...$(NC)"
	@docker rm clinical-postgres clinical-redis clinical-backend clinical-celery-worker clinical-celery-beat 2>/dev/null || true
	@echo "$(GREEN)✓ All containers removed$(NC)"
	@echo ""
	
	@echo "$(YELLOW)3. Starting infrastructure services...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.local.yml up -d postgres redis
	@echo "$(GREEN)✓ Infrastructure services started$(NC)"
	@echo ""
	
	@echo "$(YELLOW)4. Waiting for services to be ready...$(NC)"
	@echo -n "   Waiting for PostgreSQL..."
	@for i in $$(seq 1 30); do \
		if docker exec -t $$(docker ps -qf "name=postgres") pg_isready -U postgres > /dev/null 2>&1; then \
			echo " $(GREEN)✓ Ready$(NC)"; \
			break; \
		fi; \
		echo -n "."; \
		sleep 1; \
	done
	
	@echo -n "   Waiting for Redis..."
	@for i in $$(seq 1 30); do \
		if docker exec -t $$(docker ps -qf "name=redis") redis-cli ping > /dev/null 2>&1; then \
			echo " $(GREEN)✓ Ready$(NC)"; \
			break; \
		fi; \
		echo -n "."; \
		sleep 1; \
	done
	@echo ""
	
	@echo "$(YELLOW)5. Setting up database...$(NC)"
	@cd backend && \
	if [ -d "venv" ]; then \
		echo "   Using existing virtual environment"; \
	else \
		echo "   Creating virtual environment..."; \
		python3 -m venv venv; \
	fi && \
	. venv/bin/activate && \
	echo "   Installing dependencies..." && \
	pip install -q -r requirements.txt && \
	echo "   Creating database..." && \
	PGPASSWORD=changethis psql -h localhost -U postgres -c "CREATE DATABASE clinical_dashboard" 2>/dev/null || echo "   Database already exists" && \
	echo "   Running migrations..." && \
	PYTHONPATH=. alembic upgrade head && \
	echo "$(GREEN)✓ Database setup complete$(NC)"
	@echo ""
	
	@echo "$(YELLOW)6. Starting application...$(NC)"
	@cd backend && \
	. venv/bin/activate && \
	echo "   Starting FastAPI server..." && \
	nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > api.log 2>&1 & \
	echo $$! > api.pid && \
	echo "$(GREEN)✓ API server started (PID: $$(cat api.pid))$(NC)"
	
	@echo -n "   Waiting for API..."
	@for i in $$(seq 1 30); do \
		if curl -s http://localhost:8000/api/v1/utils/health-check/ > /dev/null 2>&1 || curl -s http://localhost:8000/health > /dev/null 2>&1; then \
			echo " $(GREEN)✓ Ready$(NC)"; \
			break; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo " $(RED)✗ Failed to start$(NC)"; \
			echo "   $(YELLOW)Check logs with: tail backend/api.log$(NC)"; \
			exit 1; \
		fi; \
		echo -n "."; \
		sleep 1; \
	done
	@echo ""
	
	@echo "$(YELLOW)7. Creating default admin user...$(NC)"
	@cd backend && \
	. venv/bin/activate && \
	PYTHONPATH=. python -c "from app.core.db import init_db; from sqlmodel import Session, create_engine; from app.core.config import settings; engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI)); session = Session(engine); init_db(session); session.close()" && \
	echo "$(GREEN)✓ Admin user created (admin@sagarmatha.ai / adadad123)$(NC)"
	@echo ""
	
	@echo "$(YELLOW)8. Health check results:$(NC)"
	@make health
	@echo ""
	
	@echo "$(GREEN)═══════════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)🎉 CLINICAL DASHBOARD IS UP AND RUNNING!$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(BLUE)📍 Service URLs:$(NC)"
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
		echo "$(YELLOW)No Dockerfile found, skipping build$(NC)"; \
	fi

up: ## Start all services
	@echo "$(GREEN)Starting Clinical Dashboard...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.local.yml up -d
	@echo ""
	@echo "$(YELLOW)Starting backend API...$(NC)"
	@cd backend && \
	if [ ! -d "venv" ]; then \
		python3 -m venv venv && \
		. venv/bin/activate && \
		pip install -q -r requirements.txt; \
	fi && \
	. venv/bin/activate && \
	nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > api.log 2>&1 & \
	echo $$! > api.pid
	@echo "$(GREEN)✓ Services started!$(NC)"
	@echo ""
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Adminer: http://localhost:8080"

down: ## Stop all services
	@echo "$(YELLOW)Stopping services...$(NC)"
	@if [ -f backend/api.pid ]; then \
		kill $$(cat backend/api.pid) 2>/dev/null || true; \
		rm backend/api.pid; \
		echo "$(GREEN)✓ API server stopped$(NC)"; \
	fi
	@$(DOCKER_COMPOSE) -f docker-compose.local.yml down
	@echo "$(GREEN)✓ All services stopped$(NC)"

logs: ## View logs (use: make logs service=postgres)
	@if [ -z "$(service)" ]; then \
		echo "$(YELLOW)Showing API logs (use 'make logs service=<name>' for specific service)$(NC)"; \
		tail -f backend/api.log 2>/dev/null || echo "No API logs found"; \
	else \
		$(DOCKER_COMPOSE) -f docker-compose.local.yml logs -f $(service); \
	fi

test: ## Run API tests
	@echo "$(YELLOW)Running API tests...$(NC)"
	@cd backend && \
	if [ -d "venv" ]; then \
		. venv/bin/activate && \
		python test_api.py; \
	else \
		echo "$(RED)Virtual environment not found. Run 'make up' first$(NC)"; \
	fi

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
	@echo "$(RED)║                                                            ║$(NC)"
	@echo "$(RED)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@printf "Are you absolutely sure you want to delete everything? [y/N] "; \
	read REPLY; \
	case "$$REPLY" in \
		[yY]) \
			echo "$(YELLOW)Stopping all services...$(NC)"; \
			make down; \
			echo "$(YELLOW)Removing all containers and volumes...$(NC)"; \
			$(DOCKER_COMPOSE) -f docker-compose.local.yml down -v --remove-orphans; \
			echo "$(YELLOW)Dropping database...$(NC)"; \
			PGPASSWORD=changethis psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS clinical_dashboard" 2>/dev/null || true; \
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
	@echo "$(YELLOW)Starting Celery worker...$(NC)"
	@cd backend && \
	. venv/bin/activate && \
	nohup celery -A app.core.celery_app worker --loglevel=info > celery-worker.log 2>&1 & \
	echo $$! > celery-worker.pid
	@echo "$(GREEN)✓ Celery worker started$(NC)"
	@echo ""
	@echo "$(YELLOW)Starting Celery beat...$(NC)"
	@cd backend && \
	. venv/bin/activate && \
	nohup celery -A app.core.celery_app beat --loglevel=info > celery-beat.log 2>&1 & \
	echo $$! > celery-beat.pid
	@echo "$(GREEN)✓ Celery beat started$(NC)"
	@echo ""
	@echo "$(GREEN)Development mode started!$(NC)"
	@echo "API: http://localhost:8000 (with hot reload)"
	@echo "Flower: http://localhost:5555 (Celery monitoring)"

prod: ## Start in production mode
	@echo "$(GREEN)Starting in production mode...$(NC)"
	@echo "$(YELLOW)Note: For production, use proper deployment with Docker/Kubernetes$(NC)"
	@make up

shell-api: ## Open Python shell with app context
	@cd backend && \
	. venv/bin/activate && \
	python -c "from app.models import *; from app.crud import *; from sqlmodel import Session, create_engine; from app.core.config import settings; engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI)); session = Session(engine); import IPython; IPython.embed()"

shell-db: ## Open PostgreSQL shell
	@PGPASSWORD=changethis psql -h localhost -U postgres -d clinical_dashboard

status: ## Check service status
	@echo "$(YELLOW)Service Status:$(NC)"
	@echo ""
	@echo "$(BLUE)Infrastructure:$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.local.yml ps
	@echo ""
	@echo "$(BLUE)Application:$(NC)"
	@if [ -f backend/api.pid ] && kill -0 $$(cat backend/api.pid) 2>/dev/null; then \
		echo "   API Server: $(GREEN)✓ Running$(NC) (PID: $$(cat backend/api.pid))"; \
	else \
		echo "   API Server: $(RED)✗ Stopped$(NC)"; \
	fi
	@if [ -f backend/celery-worker.pid ] && kill -0 $$(cat backend/celery-worker.pid) 2>/dev/null; then \
		echo "   Celery Worker: $(GREEN)✓ Running$(NC) (PID: $$(cat backend/celery-worker.pid))"; \
	else \
		echo "   Celery Worker: $(YELLOW)○ Not running$(NC)"; \
	fi
	@if [ -f backend/celery-beat.pid ] && kill -0 $$(cat backend/celery-beat.pid) 2>/dev/null; then \
		echo "   Celery Beat: $(GREEN)✓ Running$(NC) (PID: $$(cat backend/celery-beat.pid))"; \
	else \
		echo "   Celery Beat: $(YELLOW)○ Not running$(NC)"; \
	fi

health: ## Health check for all services
	@echo -n "   PostgreSQL: "
	@if docker exec -t $$(docker ps -qf "name=postgres") pg_isready -U postgres > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Healthy$(NC)"; \
	else \
		echo "$(RED)✗ Unhealthy$(NC)"; \
	fi
	
	@echo -n "   Redis: "
	@if docker exec -t $$(docker ps -qf "name=redis") redis-cli ping > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Healthy$(NC)"; \
	else \
		echo "$(RED)✗ Unhealthy$(NC)"; \
	fi
	
	@echo -n "   API Backend: "
	@if curl -s http://localhost:8000/api/v1/utils/health-check/ > /dev/null 2>&1 || curl -s http://localhost:8000/health > /dev/null 2>&1; then \
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
	@cd backend && \
	. venv/bin/activate && \
	PYTHONPATH=. alembic upgrade head
	@echo "$(GREEN)✓ Migrations complete$(NC)"

seed-data: ## Generate test data
	@echo "$(YELLOW)Generating test data...$(NC)"
	@cd backend && \
	. venv/bin/activate && \
	python test_api.py
	@echo "$(GREEN)✓ Test data created$(NC)"

api-logs: ## View API logs
	@tail -f backend/api.log 2>/dev/null || echo "No API logs found. Start the API first with 'make up'"

celery-logs: ## View Celery worker logs
	@tail -f backend/celery-worker.log 2>/dev/null || echo "No Celery logs found. Start dev mode with 'make dev'"

# Code quality commands
format: ## Format code with black and isort
	@echo "$(YELLOW)Formatting backend code...$(NC)"
	@cd backend && \
	if [ -d "venv" ]; then \
		. venv/bin/activate && \
		black app && \
		isort app; \
		echo "$(GREEN)✓ Code formatted$(NC)"; \
	else \
		echo "$(RED)Virtual environment not found. Run 'make up' first$(NC)"; \
	fi

lint: ## Run linting checks
	@echo "$(YELLOW)Running linting checks...$(NC)"
	@cd backend && \
	if [ -d "venv" ]; then \
		. venv/bin/activate && \
		mypy app && \
		ruff check app && \
		ruff format app --check; \
		echo "$(GREEN)✓ Linting complete$(NC)"; \
	else \
		echo "$(RED)Virtual environment not found. Run 'make up' first$(NC)"; \
	fi

test-backend: ## Run backend tests with pytest
	@echo "$(YELLOW)Running backend tests...$(NC)"
	@cd backend && \
	if [ -d "venv" ]; then \
		. venv/bin/activate && \
		pytest -v; \
		echo "$(GREEN)✓ Tests complete$(NC)"; \
	else \
		echo "$(RED)Virtual environment not found. Run 'make up' first$(NC)"; \
	fi

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