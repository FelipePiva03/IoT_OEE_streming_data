.PHONY: test test-unit test-integration test-anomaly test-cov test-watch lint format clean help

help:
	@echo "Comandos disponíveis:"
	@echo "  make test              - Roda todos os testes"
	@echo "  make test-unit         - Roda apenas testes unitários"
	@echo "  make test-integration  - Roda testes de integração"
	@echo "  make test-anomaly      - Roda testes de anomalias"
	@echo "  make test-cov          - Roda testes com cobertura"
	@echo "  make test-watch        - Roda testes em modo watch"
	@echo "  make lint              - Verifica código com flake8"
	@echo "  make format            - Formata código com black"
	@echo "  make clean             - Remove arquivos temporários"
	@echo "  make install           - Instala dependências"

install:
	pip install -r requirements.txt

test:
	pytest -v

test-unit:
	pytest -m "unit" -v

test-integration:
	pytest -m "integration" -v

test-anomaly:
	pytest -m "anomaly" -v

test-simulator:
	pytest -m "simulator" -v

test-state-machine:
	pytest -m "state_machine" -v

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing

test-cov-xml:
	pytest --cov=src --cov-report=xml

test-watch:
	ptw -- -v

test-parallel:
	pytest -n auto -v

lint:
	flake8 src tests --max-line-length=127 --extend-ignore=E203,W503

format:
	black src tests

format-check:
	black --check src tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage coverage.xml

run-simulator:
	python -m src.producer.main

run-tests-quick:
	pytest -m "unit and not slow" -v

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d zookeeper kafka schema-registry kafka-ui

docker-down:
	docker-compose down

docker-simulator-normal:
	docker-compose --profile normal up

docker-simulator-monthly:
	docker-compose --profile monthly up

docker-simulator-ultra-fast:
	docker-compose --profile ultra-fast up

all: clean install test lint
