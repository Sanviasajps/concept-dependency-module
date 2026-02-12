import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect("python_learning.db")
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS concepts (
    concept_id TEXT PRIMARY KEY,
    name TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS concept_dependencies (
    concept_id TEXT,
    prerequisite_id TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS knowledge_state (
    learner_id TEXT,
    mastery TEXT,
    timestamp TEXT
);
""")

# Insert sample concepts
concepts = [
    ("P1", "Variables"),
    ("P2", "Loops"),
    ("P3", "Functions")
]

cursor.executemany("INSERT INTO concepts VALUES (?, ?)", concepts)

# Insert dependencies
dependencies = [
    ("P2", "P1"),
    ("P3", "P2")
]

cursor.executemany("INSERT INTO concept_dependencies VALUES (?, ?)", dependencies)

# Insert mastery
mastery_data = {
    "P1": 0.9,
    "P2": 0.3
}

cursor.execute(
    "INSERT INTO knowledge_state VALUES (?, ?, ?)",
    ("L1", json.dumps(mastery_data), datetime.now().isoformat())
)

conn.commit()
conn.close()

print("Database created successfully!")
