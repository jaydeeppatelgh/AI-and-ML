import schedule
import time
from agents.hospital_finder import HospitalFinderAgent
from agents.requirement_analyzer import RequirementAnalyzer
from agents.database_manager import DatabaseManager
from agents.communication_agent import CommunicationAgent

def job():
    raw_data = hospital_finder.fetch_sources()
    for item in raw_data:
        analyzed = analyzer.analyze(item['link'])
        if analyzed['name']:
            db_manager.save_lead(analyzed)
            comm_agent.send_email(item['link'], "New Pharma Products", f"Dear {analyzed['name']}, we offer the products you need.")
            print(f"Notification sent to {analyzed['name']}")

hospital_finder = HospitalFinderAgent(['https://example.com/news'])
analyzer = RequirementAnalyzer()
db_manager = DatabaseManager()
comm_agent = CommunicationAgent('smtp.gmail.com', 587, 'your_email@gmail.com', 'your_password')

schedule.every(1).hour.do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
