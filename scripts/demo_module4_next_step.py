import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import sqlite3

from tutor.policy.next_step_policy import recommend_next_step


TUTOR_DB_PATH = "tutor.db"

CONCEPT_DB_PATHS = [
    "Cognitive_databases/python_learning.db",
    "Cognitive_databases/database_sql.db",
    "Cognitive_databases/html_web_basics.db",
    "Cognitive_databases/git_version_control.db",
    "Cognitive_databases/data_structures.db",
]

LEARNER_ID = "S1"


def main():
    conn = sqlite3.connect(TUTOR_DB_PATH)

    try:
        result = recommend_next_step(
            learner_id=LEARNER_ID,
            tutor_conn=conn,
            concept_db_paths=CONCEPT_DB_PATHS,
        )

        print(json.dumps(result, indent=2))

    finally:
        conn.close()


if __name__ == "__main__":
    main()
