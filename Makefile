.PHONY: setup install seed dev dev-backend dev-frontend

# First-time setup
setup:
	cp .env.example .env
	cd backend && pip install -r requirements.txt
	cd frontend && npm install
	@echo "✅ Setup complete. Edit .env with your API keys."

# Install dependencies
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# Ingest RAG documents into Pinecone
ingest-rag:
	cd backend && python -m rag.ingest

# Create tables in Supabase
init-db:
	@echo "Run schema.sql in Supabase SQL Editor"

# Seed data + run batch (ONE TIME only, before first demo)
seed:
	cd backend && python -m simulation.batch_runner

# Start development servers
dev: dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# Start ngrok tunnel for webhooks
tunnel:
	ngrok http 8000
