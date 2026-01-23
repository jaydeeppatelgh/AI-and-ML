import os
import psycopg2
import json
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set in env")
    # return a new connection (caller should .close())
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def find_or_create_client(conn, name):
    """
    Returns client id (uuid) for client name. Creates client if missing.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM clients WHERE name = %s", (name,))
        r = cur.fetchone()
        if r:
            return r[0]
        cur.execute("INSERT INTO clients(name) VALUES (%s) RETURNING id", (name,))
        cid = cur.fetchone()[0]
        conn.commit()
        return cid

def update_client_contacts(conn, client_id, email: str | None = None, contacts_update: dict | None = None):
    """
    Merge a contact/email into the `clients.contacts` JSON column.

    If `contacts_update` is provided it will be merged into the existing
    contacts dict. If `email` is provided it will be added into an
    `emails` array (creating it if necessary) and de-duplicated.

    This function commits the change.
    """
    if client_id is None:
        return
    with conn.cursor() as cur:
        cur.execute("SELECT contacts FROM clients WHERE id=%s", (client_id,))
        row = cur.fetchone()
        existing = row[0] if row and row[0] else {}
        if not isinstance(existing, dict):
            existing = {}

        # Merge provided contacts_update dict
        if contacts_update and isinstance(contacts_update, dict):
            for k, v in contacts_update.items():
                existing[k] = v

        # Add email into emails list if provided
        if email:
            emails = existing.get("emails")
            if not isinstance(emails, list):
                emails = []
            if email not in emails:
                emails.append(email)
            existing["emails"] = emails

        cur.execute("UPDATE clients SET contacts = %s WHERE id = %s", (json.dumps(existing), client_id))
        conn.commit()
