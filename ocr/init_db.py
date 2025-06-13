import sqlite3
from datetime import datetime

def create_new_database():
    conn = sqlite3.connect('complaints.db')
    cursor = conn.cursor()
    
    # Create complaints table with updated schema
    cursor.execute("""
    CREATE TABLE complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        problem TEXT NOT NULL,
        address TEXT NOT NULL,
        contact_no TEXT NOT NULL,
        error_code TEXT,
        media_path TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending',
        predicted_solution TEXT,
        needs_engineer INTEGER
    )
    """)
    
    # Create technicians table
    cursor.execute("""
    CREATE TABLE technicians (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact_no TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        status TEXT DEFAULT 'available',
        specialization TEXT
    )
    """)
    
    # Insert sample technicians
    sample_technicians = [
        ('Ravi Patil', '9876543210', 19.0952, 74.7496, 'available', 'AC,Refrigerator'),
        ('Neha Joshi', '9898989898', 19.1033, 74.7412, 'available', 'TV,Washing Machine'),
        ('Ankit Sharma', '9123456780', 19.1111, 74.7555, 'available', 'Induction,Microoven')
    ]
    
    cursor.executemany("""
    INSERT INTO technicians (name, contact_no, latitude, longitude, status, specialization)
    VALUES (?, ?, ?, ?, ?, ?)
    """, sample_technicians)
    
    conn.commit()
    conn.close()
    print("✅ New database created successfully with correct schema")

if __name__ == "__main__":
    create_new_database()