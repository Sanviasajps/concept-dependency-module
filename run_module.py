from tutor.concept_dependency import run_concept_dependency_module


db_paths = [
    "Cognitive_databases/python_learning.db",
    "Cognitive_databases/database_sql.db",
    "Cognitive_databases/html_web_basics.db",
    "Cognitive_databases/git_version_control.db",
    "Cognitive_databases/data_structures.db"
]


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
