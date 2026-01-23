# AI-and-ML Repository

A comprehensive collection of AI and machine learning projects showcasing various applications including chatbots, recommendation systems, monitoring services, and more.

## Projects Overview

### 1. **AI Chatbot With RAG**
An intelligent chatbot system with Retrieval-Augmented Generation (RAG) capabilities. Containerized microservices architecture with dedicated API, frontend, and ETL services.

**Stack**: FastAPI, Neo4j, Docker, Docker Compose
- `chatbot_api/` - FastAPI backend service
- `chatbot_frontend/` - Frontend application
- `hospital_neo4j_etl/` - ETL pipeline for Neo4j data

---

### 2. **Tiny Helper - Event Monitoring API Agent**
An intelligent error monitoring and digest service for e-commerce platforms. Ingests error events, analyzes patterns, generates AI-powered recommendations, and sends automated digest reports via email and Slack.

**Features**:
- Real-time event ingestion with bulk support
- AI-powered error analysis using OpenAI
- Automated email and Slack notifications
- Multi-tenant architecture with API key authentication
- PostgreSQL with JSONB storage
- Scheduled digest generation

**Stack**: FastAPI, PostgreSQL, OpenAI, SendGrid, Slack API

---

### 3. **EV Charging Recommender AI**
A machine learning system for recommending electric vehicle charging stations based on user preferences and location data.

**Stack**: Python, scikit-learn, pandas
- `api/` - REST API service
- `core/` - Recommendation engine
- `ml/` - Model training pipeline

---

### 4. **LLM-DataQA**
Question-answering system powered by LLMs for data analysis and querying across multiple datasets.

**Datasets**:
- AI financial data
- AI models information
- Space missions data
- Student records

---

### 5. **FSM-Driven Voice Agent**
A finite state machine-based voice agent system for handling complex conversation flows with webhook integration.

**Features**:
- State machine-driven conversation logic
- Webhook engine for integrations
- Configuration-based intake handling
- Transcript logging
- Async request handling

---

### 6. **Smart Bundle AI Agent**
An intelligent agent system for product bundle recommendations and smart bundling solutions.

**Stack**: Python, Flask/FastAPI, AI/ML

---

### 7. **Pharma AI Agent**
AI-powered scheduling and workflow agent for pharmaceutical operations and management.

---

### 8. **AI Blog Content PDF Generator**
Automated tool for generating blog content and converting it to PDF format using AI.

---

### 9. **Trading Pattern Service**
A service for analyzing trading patterns and providing market insights with database storage and API endpoints.

**Stack**: FastAPI, PostgreSQL, Docker, SQL schema management

---

### 10. **Next.js Samples**
Collection of Next.js applications demonstrating modern web development patterns:
- `next-supabase-auth/` - Authentication with Supabase
- `nextjs-async-workflow/` - Asynchronous workflow handling
- `nextjs-modular-components/` - Component architecture
- `nextjs-apps-script/` - Google Apps Script integration
- `vercel-api-tools/` - Vercel API utilities

---

## Setup Instructions

### Prerequisites
- Python 3.10+ (for Python projects)
- Node.js 18+ (for Next.js projects)
- PostgreSQL (for projects requiring a database)
- Docker & Docker Compose (for containerized projects)

### General Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/jaydeeppatelgh/AI-and-ML.git
   cd AI-and-ML
   ```

2. **Navigate to a project directory**
   ```bash
   cd <project-name>
   ```

3. **Install dependencies** (Python projects)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the project** (check individual project READMEs for specific instructions)

## .gitignore

This repository includes a comprehensive `.gitignore` that excludes:
- Virtual environments (`venv/`, `env/`)
- Environment files (`.env`, `.env.local`)
- Python cache and build files
- IDE configurations and logs
- OS-specific files

## Contributing

Feel free to explore, modify, and enhance these projects. Each project has its own README with detailed documentation.

## License

Check individual project directories for license information.

## Author

**jaydeeppatelgh**
