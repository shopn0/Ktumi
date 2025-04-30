import sqlite3
from models.contact import Contact, ContactSummary

DB_NAME = "contacts.db"

# Database connection

def connect():
    return sqlite3.connect(DB_NAME)

# Initialize schema with migrations

def init_db():
    conn = connect()
    cursor = conn.cursor()

    # Create contacts table if missing
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
    """
    )

    # Create attachments table if missing
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        FOREIGN KEY(contact_id) REFERENCES contacts(id) ON DELETE CASCADE
    );
    """
    )

    # Migrate: add missing columns to contacts table
    cursor.execute("PRAGMA table_info(contacts)")
    existing = {row[1] for row in cursor.fetchall()}
    for col in ("present_address", "permanent_address", "driver_license",
                "passport_no", "nid_no", "notes", "profile_pic"):
        if col not in existing:
            cursor.execute(f"ALTER TABLE contacts ADD COLUMN {col} TEXT;")

    conn.commit()
    conn.close()

# CRUD operations

def get_all_contacts():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, name, phone, profile_pic FROM contacts")
    rows = c.fetchall()
    conn.close()
    return [ContactSummary(id=r[0], name=r[1], phone=r[2], profile_pic=r[3]) for r in rows]


def get_contact_by_id(contact_id: int):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, phone, present_address, permanent_address,
               driver_license, passport_no, nid_no, notes, profile_pic
        FROM contacts WHERE id = ?
    """, (contact_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    contact = Contact(
        name=row[1],
        phone=row[2],
        present_address=row[3] or "",
        permanent_address=row[4] or "",
        driver_license=row[5] or "",
        passport_no=row[6] or "",
        nid_no=row[7] or "",
        notes=row[8] or "",
        profile_pic=row[9] or "",
        attachments=[]
    )
    # Load attachments paths
    c.execute("SELECT file_path FROM attachments WHERE contact_id = ?", (contact_id,))
    contact.attachments = [r[0] for r in c.fetchall()]
    conn.close()
    return contact


def add_contact(contact: Contact):
    conn = connect()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO contacts (name, phone, present_address, permanent_address,
                               driver_license, passport_no, nid_no, notes, profile_pic)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contact.name,
            contact.phone,
            contact.present_address,
            contact.permanent_address,
            contact.driver_license,
            contact.passport_no,
            contact.nid_no,
            contact.notes,
            contact.profile_pic
        )
    )
    cid = c.lastrowid
    for path in contact.attachments:
        c.execute(
            "INSERT INTO attachments (contact_id, file_path) VALUES (?, ?)",
            (cid, path)
        )
    conn.commit()
    conn.close()


def update_contact(contact_id: int, contact: Contact):
    conn = connect()
    c = conn.cursor()
    c.execute(
        """
        UPDATE contacts SET
            name = ?, phone = ?, present_address = ?, permanent_address = ?,
            driver_license = ?, passport_no = ?, nid_no = ?, notes = ?, profile_pic = ?
        WHERE id = ?
        """, (
            contact.name,
            contact.phone,
            contact.present_address,
            contact.permanent_address,
            contact.driver_license,
            contact.passport_no,
            contact.nid_no,
            contact.notes,
            contact.profile_pic,
            contact_id
        )
    )
    # Replace attachments
    c.execute("DELETE FROM attachments WHERE contact_id = ?", (contact_id,))
    for path in contact.attachments:
        c.execute(
            "INSERT INTO attachments (contact_id, file_path) VALUES (?, ?)",
            (contact_id, path)
        )
    conn.commit()
    conn.close()


def delete_contact(contact_id: int):
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM attachments WHERE contact_id = ?", (contact_id,))
    c.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    conn.commit()
    conn.close()
