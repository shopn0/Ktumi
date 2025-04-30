import sqlite3
from models.contact import Contact

DB_NAME = "contacts.db"

def connect():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = connect()
    cursor = conn.cursor()

    # Main contacts table with all fields
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        present_address TEXT,
        permanent_address TEXT,
        driver_license TEXT,
        passport_no TEXT,
        nid_no TEXT,
        notes TEXT,
        profile_pic TEXT
    );
    """)

    # Attachments table (one row per file)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        FOREIGN KEY(contact_id) REFERENCES contacts(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
def add_contact(contact):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO contacts
          (name, phone, present_address, permanent_address,
           driver_license, passport_no, nid_no, notes, profile_pic)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        contact.name, contact.phone, contact.present_address,
        contact.permanent_address, contact.driver_license,
        contact.passport_no, contact.nid_no, contact.notes,
        contact.profile_pic
    ))
    contact_id = c.lastrowid
    # Attachments
    for path in contact.attachments:
        c.execute(
            "INSERT INTO attachments (contact_id, file_path) VALUES (?, ?)",
            (contact_id, path)
        )
    conn.commit()
    conn.close()

def get_all_contacts():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, name, phone, profile_pic FROM contacts")
    rows = c.fetchall()
    conn.close()
    return [Contact(*row) for row in rows]


def add_dummy_contacts():
    conn = connect()
    cursor = conn.cursor()
    for i in range(5):
        cursor.execute("INSERT INTO contacts (name, phone) VALUES (?, ?)", (f"Person {i+1}", f"017000000{i}"))
    conn.commit()
    conn.close()
