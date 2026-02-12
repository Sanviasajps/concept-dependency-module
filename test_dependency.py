import sqlite3
import json

from src.core.dependency.dependency_matrix import (
    get_unlocked_concepts,
    get_blocked_concepts
)

PREREQ_THRESHOLD = 0.60

# ⚠️ Change this if needed to match an existing student_id in tutor.db
learner_id = "S1"


# Connect to your friend's tutor.db
conn = sqlite3.connect("Cognitive_databases/database/tutor.db")
cursor = conn.cursor()

# Fetch latest mastery JSON from knowledge_state
cursor.execute("""
    SELECT state_json
    FROM knowledge_state
    WHERE student_id = ?
    ORDER BY updated_at DESC
    LIMIT 1
""", (learner_id,))

row = cursor.fetchone()

if row:
    mastery_vector = json.loads(row[0])
else:
    print(f"No knowledge state found for student_id = {learner_id}")
    mastery_vector = {}

# Get unlocked and blocked concepts
unlocked = get_unlocked_concepts(mastery_vector, PREREQ_THRESHOLD, conn)
blocked = get_blocked_concepts(mastery_vector, PREREQ_THRESHOLD, conn)

print("Unlocked Concepts:", unlocked)
print("Blocked Concepts:", blocked)

conn.close()
