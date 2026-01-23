# What it is: A built-in module for working with JSON data (JavaScript Object Notation), a common format for data exchange.
# import json
# data = {"name": "Alice", "age": 30}
# json_str = json.dumps(data)  # Convert dict to JSON string
# print(json_str)  # Output: {"name": "Alice", "age": 30}
# back_to_dict = json.loads(json_str)  # Convert back to dict
# print(back_to_dict)  # Output: {'name': 'Alice', 'age': 30}

# What it is: A library for making HTTP requests (e.g., to websites/APIs). Not built-in; install with pip install requests.
# import requests
# response = requests.get("https://api.example.com/data")  # Fetch data from a URL
# print(response.json())  # Output: JSON data from the API

# What it is: A built-in module for recording messages (logs) about what's happening in your program.
# import logging
# logging.basicConfig(level=logging.INFO)
# logging.info("App started")  # Writes "INFO: App started" to console/logs

# What it is: A built-in module for HMAC (Hash-based Message Authentication Code), used for secure token verification.
# import hmac # HMAC (Hash-based Message Authentication Code)
# import hashlib
# key = b"secret"
# message = b"hello"
# digest = hmac.new(key, message, hashlib.sha256).hexdigest()  # Creates a secure hash
# print(digest)  # Output: a long hex string for verification

# What it is: A library for connecting to PostgreSQL databases. Not built-in; install with pip install psycopg2.
# import psycopg2
# conn = psycopg2.connect("dbname=tiny_helper_db user=postgres")  # Connect to DB
# cur = conn.cursor()
# cur.execute("SELECT * FROM clients")  # Run a query
# print(cur.fetchall())  # Output: list of rows

# What it is: A built-in module for generating secure random numbers/tokens.
# import secrets
# token = secrets.token_hex(16)  # Generate a random 32-char hex string
# print(token)  # Output: something like "a1b2c3d4e5f67890abcdef1234567890"

# What it is: A built-in module for handling HTML (escaping special characters).
# import html
# unsafe = "<script>alert('hack')</script>"
# safe = html.escape(unsafe)  # Escapes < > & etc.
# print(safe)  # Output: &lt;script&gt;alert(&#x27;hack&#x27;)&lt;/script&gt;

# What it is: Built-in classes for dates/times.
# from datetime import datetime, timedelta
# now = datetime.now()  # Current time
# later = now + timedelta(days=1)  # Add 1 day
# print(later)  # Output: tomorrow's date/time

# What it is: Built-in type hints for better code clarity (Python 3.5+).
# from typing import Optional, List
# def greet(name: Optional[str] = None) -> str:
#     return f"Hello, {name or 'world'}!"
# names: List[str] = ["Alice", "Bob"]
# print(greet())  # Output: Hello, world!

# What it is: FastAPI framework for building APIs. Not built-in; install with pip install fastapi.
# from fastapi import FastAPI
# app = FastAPI()
# @app.get("/")
# def home():
#     return {"message": "Hello"}
# # Run with uvicorn to serve at http://localhost:8000/

# What it is: Library for data validation/models. Not built-in; install with pip install pydantic.
from pydantic import BaseModel, Field
class User(BaseModel):
    name: str = Field(min_length=1)
    age: int = Field(ge=0)
user = User(name="Alice", age=30)  # Validates input
print(user.name)  # Output: Alice







