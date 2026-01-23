# Tiny Helper

Intelligent Error Monitoring and Digest Service for E-commerce Platforms

Tiny Helper is a FastAPI-based service designed to ingest error events from client applications, analyze error patterns, generate AI-powered recommendations, and send automated digest reports via email and Slack notifications. It's particularly suited for e-commerce integrations where monitoring data flows between systems is critical.

## Features

- **Event Ingestion**: Ingest single or bulk error events with detailed metadata
- **Real-time Alerts**: Immediate Slack notifications for critical errors
- **AI-Powered Analysis**: OpenAI-powered recommendations for error resolution
- **Automated Digests**: Scheduled or on-demand error digest generation
- **Professional Email Reports**: HTML-formatted digest emails with pricing CTAs
- **Client Management**: Multi-tenant architecture with API key authentication
- **PostgreSQL Storage**: Robust data persistence with JSONB support
- **Comprehensive Logging**: Detailed logging to files with configurable levels

## Architecture

- **Backend**: FastAPI (Python async web framework)
- **Database**: PostgreSQL with JSONB for flexible metadata storage
- **Authentication**: Bearer token authentication with client isolation
- **Notifications**: SendGrid for emails, Slack webhooks for alerts
- **AI**: OpenAI GPT-4o-mini for error analysis and recommendations
- **Deployment**: Uvicorn ASGI server

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jaydeeppatelai/Tiny-helper.git
   cd tiny-helper
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   DATABASE_URL=postgres://user:password@localhost:5432/tiny_helper_db
   INGEST_TOKEN=your_admin_token_here
   SENDGRID_API_KEY=your_sendgrid_api_key
   FROM_EMAIL=noreply@yourdomain.com
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   OPENAI_API_KEY=your_openai_api_key
   PORT=8000
   ```

5. **Set up database**
   ```bash
   psql "$DATABASE_URL" -f create_tables.sql
   ```

6. **Run the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## API Endpoints

### Core Endpoints

#### `GET /`
Returns basic API information and documentation links.

#### `POST /events`
Ingest a single error event.

**Authentication**: Client API key (Bearer token)

**Request Body**:
```json
{
  "client_id": "uuid-string",
  "flow": "WooCommerce → Zoho",
  "entity_type": "order",
  "entity_id": "SO-12811",
  "status": "fail",
  "occurred_at": "2025-01-22T10:30:00Z",
  "severity": "critical",
  "message": "SKU not found for item ABC-123",
  "meta": {
    "customer_email": "customer@example.com",
    "order_total": 99.99
  }
}
```

**Response**:
```json
{
  "ok": true,
  "client_id": "uuid-string",
  "event_id": 12345
}
```

#### `POST /events/bulk`
Ingest multiple events in a single request (up to 50 events).

**Authentication**: Client API key (Bearer token)

**Request Body**: Array of event objects

**Response**:
```json
{
  "ok": true,
  "client_id": "uuid-string",
  "received": 3,
  "inserted": 3,
  "event_ids": [12345, 12346, 12347],
  "failed": []
}
```

### Digest Management

#### `POST /digests/run/all`
Trigger digest generation for all clients (admin only).

**Authentication**: Admin token (Bearer token)

**Request Body**:
```json
{
  "window_days": 1,
  "window_minutes": null,
  "schedule_label": "daily"
}
```

#### `POST /digests/run/{client_id}`
Trigger digest generation for a specific client.

**Authentication**: Admin token or client API key

### Client Management

#### `POST /clients`
Create a new client (admin only).

**Authentication**: Admin token (Bearer token)

**Request Body**:
```json
{
  "name": "Acme Corp",
  "contacts": {
    "emails": ["admin@acme.com", "support@acme.com"],
    "slack_webhook": "https://hooks.slack.com/services/..."
  }
}
```

**Response**:
```json
{
  "ok": true,
  "client_id": "uuid-string",
  "api_key": "generated-api-key",
  "name": "Acme Corp"
}
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `INGEST_TOKEN` | Admin authentication token | Yes | - |
| `SENDGRID_API_KEY` | SendGrid API key for email sending | No | - |
| `FROM_EMAIL` | Sender email address for notifications | No | - |
| `SLACK_WEBHOOK_URL` | Slack webhook URL for alerts | No | - |
| `OPENAI_API_KEY` | OpenAI API key for AI recommendations | No | - |
| `PORT` | Server port | No | 8000 |

### Database Schema

The application uses three main tables:

- **clients**: Stores client information, API keys, and contact details
- **events**: Stores all ingested error events with metadata
- **digests**: Stores generated digest reports and their statistics

Run `create_tables.sql` to initialize the database schema.

## Usage Examples

### Ingesting an Event

```bash
curl -X POST http://localhost:8000/events \
  -H "Authorization: Bearer YOUR_CLIENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "your-client-uuid",
    "flow": "Shopify → ERP",
    "entity_type": "product",
    "entity_id": "PROD-001",
    "status": "fail",
    "occurred_at": "2025-01-22T15:45:00Z",
    "message": "Product variant not found in ERP",
    "severity": "warning"
  }'
```

### Creating a Client

```bash
curl -X POST http://localhost:8000/clients \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Client Inc",
    "contacts": {
      "emails": ["contact@newclient.com"]
    }
  }'
```

### Running a Digest

```bash
curl -X POST http://localhost:8000/digests/run/all \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "window_days": 7,
    "schedule_label": "weekly_report"
  }'
```

## Error Analysis & AI Recommendations

Tiny Helper uses OpenAI's GPT-4o-mini to analyze error patterns and provide actionable recommendations. The AI:

- Explains errors in simple, non-technical language
- Provides 2-4 practical next steps for resolution
- Focuses on e-commerce operations context
- Avoids technical jargon

Example AI recommendation:
```
"Product variant not found in ERP → What this means: Your online store is trying to update a product that doesn't exist in your inventory system. Next steps: 1) Check if the product was recently deleted from your ERP. 2) Verify the product code matches exactly. 3) Add the product to your ERP if it's missing. 4) Contact your ERP administrator if the issue persists."
```

## Notifications

### Email Digests
- Professional HTML templates with error statistics
- Top error reasons and counts
- AI-powered recommendations
- Pricing CTAs for service upgrades
- Sent to client contact emails

### Slack Alerts
- Immediate notifications for critical errors
- Formatted messages with error details
- Includes metadata preview when available

## Logging

Logs are written to `logs/tiny-helper.log` with the following format:
```
2025-01-22 10:30:00,123 [INFO] tiny-helper: Email sent successfully to admin@example.com, support@example.com: 202
```

Log levels: DEBUG, INFO, WARNING, ERROR

## Development

### Project Structure
```
tiny-helper/
├── main.py              # FastAPI application and endpoints
├── db.py                # Database connection and utilities
├── learn.py             # Learning examples (development)
├── requirements.txt     # Python dependencies
├── create_tables.sql    # Database schema
├── logs/                # Log files directory
├── README.md           # This file
└── .env                # Environment variables (create locally)
```

### Running Tests
```bash
# Install test dependencies if needed
pip install pytest httpx

# Run tests (add test files as needed)
pytest
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Deployment

### Production Considerations

1. **Environment Variables**: Never commit API keys to version control
2. **Database**: Use connection pooling for high traffic
3. **Logging**: Configure log rotation and monitoring
4. **Security**: Use HTTPS in production, validate all inputs
5. **Scaling**: Consider using Redis for background task queuing

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

- **Database connection failed**: Check `DATABASE_URL` format and PostgreSQL availability
- **Authentication errors**: Verify tokens are correct and properly formatted
- **Email not sending**: Check SendGrid API key and FROM_EMAIL configuration
- **AI recommendations failing**: Verify OpenAI API key and network connectivity

### Debug Mode
Set logging level to DEBUG in `main.py` for detailed request/response logging.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is proprietary. Contact the maintainers for usage permissions.

## Support

- **Documentation**: Visit `/docs` endpoint when running locally
- **Issues**: Create GitHub issues for bugs and feature requests
- **Email**: support@tiny-helper.io
- **Website**: https://tiny-helper.io

---

**Version**: MVP
**Last Updated**: January 2026
