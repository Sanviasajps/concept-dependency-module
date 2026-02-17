import sys
from tutor.concept_dependency import run_concept_dependency_module


# -------------------------------------------------------
# Configure DB paths (same as run_module.py)
# -------------------------------------------------------

db_paths = [
    "Cognitive_databases/python_learning.db",
    "Cognitive_databases/database_sql.db",
    "Cognitive_databases/html_web_basics.db",
    "Cognitive_databases/git_version_control.db",
    "Cognitive_databases/data_structures.db"
]


# -------------------------------------------------------
# Run Module 3
# -------------------------------------------------------

result = run_concept_dependency_module(db_paths)


# -------------------------------------------------------
# 1️⃣ Check for Cycles
# -------------------------------------------------------

if not result["is_dag"]:
    print("❌ VALIDATION FAILED: Cycles detected in concept graph.")
    print("Cycles:", result["cycles"])
    sys.exit(1)


# -------------------------------------------------------
# 2️⃣ Check for Missing Concept References
# -------------------------------------------------------

invalid_edges = []

for edge in result["edges"]:
    p = edge["prerequisite_id"]
    c = edge["concept_id"]

    if p not in result["concept_index"] or c not in result["concept_index"]:
        invalid_edges.append(edge)

if invalid_edges:
    print("❌ VALIDATION FAILED: Invalid concept references found.")
    print(invalid_edges)
    sys.exit(1)


# -------------------------------------------------------
# ✅ If All Good
# -------------------------------------------------------

print("✅ Graph Validation PASSED")
print("Total Concepts:", len(result["concept_index"]))
print("Total Edges:", len(result["edges"]))
sys.exit(0)
