from tutor.concept_dependency import (
    run_concept_dependency_module,
    compute_unlocked_and_blocked
)

# =========================================================
# Database Paths
# =========================================================

db_paths = [
    "Cognitive_databases/python_learning.db",
    "Cognitive_databases/database_sql.db",
    "Cognitive_databases/html_web_basics.db",
    "Cognitive_databases/git_version_control.db",
    "Cognitive_databases/data_structures.db"
]

# =========================================================
# Run Module 3
# =========================================================

result = run_concept_dependency_module(db_paths)

print("--------------------------------------------------")
print("Concept Dependency Module Output")
print("--------------------------------------------------")

print("Is DAG:", result["is_dag"])
print("Total Concepts:", len(result["concept_index"]))
print("Total Edges:", len(result["edges"]))
print("Topological Order (first 10):", result["topological_order"][:10])

if not result["is_dag"]:
    print("Cycles detected:", result["cycles"])

# =========================================================
# XAI — Unlock & Blocked Reason Test
# =========================================================

print("\n--------------------------------------------------")
print("Unlock / Blocked (XAI Output)")
print("--------------------------------------------------")

reverse_adj = result["reverse_adjacency"]

# Example mastery dictionary (for testing)
# You can change values to test behavior
mastery = {
    "P1": 0.8,
    "P2": 0.4,
    "D1": 0.9,
    "S1": 0.6
}

unlock_info = compute_unlocked_and_blocked(
    reverse_adj,
    mastery,
    threshold=0.7
)

print("Unlocked Concepts:", unlock_info["unlocked"])
print("\nBlocked Concepts With Reasons:")

for item in unlock_info["blocked"]:
    print(item)
