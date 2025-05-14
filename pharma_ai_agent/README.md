# AI Agent for Pharma & Hospitals

## Objective:
Develop an AI Agent to assist pharmaceutical companies by identifying new hospitals and medical stores. The agent continuously scans online data sources, extracts relevant information, and sends notifications about available pharmaceutical products and services.

## Components:
1. **HospitalFinderAgent**: Scrapes online sources to find new hospitals and stores.
2. **RequirementAnalyzer**: Uses NLP to extract contact info and understand the needs of hospitals and stores.
3. **DatabaseManager**: Saves leads and communication history using SQLite.
4. **CommunicationAgent**: Sends email notifications to the identified leads.

## Technologies Used:
- **Web Scraping**: BeautifulSoup, requests
- **NLP**: spaCy
- **Database**: SQLite
- **Email Communication**: smtplib
- **Task Scheduling**: schedule
- **Environment**: Python 3.x

## Setup:
1. Install the required libraries:
   ```bash
   pip install requests beautifulsoup4 spacy smtplib sqlalchemy schedule
