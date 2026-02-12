import sqlite3
import json

from src.core.dependency.dependency_matrix import (
    get_unlocked_concepts,
    get_blocked_concepts
)

PREREQ_THRESHOLD = 0.60
learner_id = "L1"

conn = sqlite3.connect("python_learning.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT mastery
    FROM knowledge_state
    WHERE learner_id = ?
    ORDER BY timestamp DESC
    LIMIT 1
""", (learner_id,))

row = cursor.fetchone()

if row:
    mastery_vector = json.loads(row[0])
else:
    mastery_vector = {}

unlocked = get_unlocked_concepts(mastery_vector, PREREQ_THRESHOLD, conn)
blocked = get_blocked_concepts(mastery_vector, PREREQ_THRESHOLD, conn)

print("Unlocked Concepts:", unlocked)
print("Blocked Concepts:", blocked)

conn.close()
