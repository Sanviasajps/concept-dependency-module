import sqlite3
from collections import defaultdict, deque
from typing import Dict, List, Tuple


# =========================================================
# A) Load Concepts and Dependencies from Multiple DB Files
# =========================================================

def load_concepts_and_edges(db_paths: List[str]) -> Tuple[Dict[str, dict], List[dict]]:
    concepts = {}
    edges = []

    for db_path in db_paths:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # -------------------------------
        # Load Concepts
        # -------------------------------
        cursor.execute(
            "SELECT concept_id, name, difficulty, description FROM concepts"
        )

        for row in cursor.fetchall():
            concept_id = row[0]
            concepts[concept_id] = {
                "concept_id": concept_id,
                "name": row[1],
                "difficulty": row[2],
                "description": row[3],
            }

        # -------------------------------
        # Load Dependencies
        # -------------------------------
        try:
            cursor.execute(
                "SELECT concept_id, prerequisite_id, weight FROM concept_dependencies"
            )
        except Exception:
            cursor.execute(
                "SELECT concept_id, prerequisite_id, 1.0 as weight FROM concept_dependencies"
            )

        for row in cursor.fetchall():
            edges.append({
                "concept_id": row[0],
                "prerequisite_id": row[1],
                "weight": float(row[2]) if row[2] is not None else 1.0,
                "source_db": db_path
            })

        conn.close()

    return concepts, edges


# =========================================================
# B) Build Graph + Matrix + Cycle Detection
# =========================================================

def build_dependency_graph(concepts: Dict[str, dict], edges: List[dict]) -> dict:

    adjacency = defaultdict(list)
    reverse_adjacency = defaultdict(list)
    valid_edges = []

    # Validate edges
    for edge in edges:
        p = edge["prerequisite_id"]
        c = edge["concept_id"]

        if p in concepts and c in concepts:
            adjacency[p].append(c)
            reverse_adjacency[c].append(p)
            valid_edges.append(edge)

    # Stable ordering
    concept_ids = sorted(concepts.keys())
    concept_index = {cid: i for i, cid in enumerate(concept_ids)}
    index_concept = concept_ids.copy()

    n = len(concept_ids)

    # Build matrix
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]

    for edge in valid_edges:
        i = concept_index[edge["prerequisite_id"]]
        j = concept_index[edge["concept_id"]]
        matrix[i][j] = edge["weight"]

    # ------------------------------------------------------
    # Cycle Detection (DFS Coloring)
    # ------------------------------------------------------

    visited = {}
    stack = []
    cycles = []
    is_dag = True

    def dfs(node):
        nonlocal is_dag
        visited[node] = 1
        stack.append(node)

        for neighbor in adjacency[node]:
            state = visited.get(neighbor, 0)

            if state == 0:
                dfs(neighbor)
            elif state == 1:
                is_dag = False
                cycle_start = stack.index(neighbor)
                cycles.append(stack[cycle_start:] + [neighbor])

        stack.pop()
        visited[node] = 2

    for cid in concept_ids:
        if visited.get(cid, 0) == 0:
            dfs(cid)

    # ------------------------------------------------------
    # Topological Sort (only if DAG)
    # ------------------------------------------------------

    topo_order = []

    if is_dag:
        in_degree = {cid: 0 for cid in concept_ids}

        for p in adjacency:
            for c in adjacency[p]:
                in_degree[c] += 1

        queue = deque([cid for cid in concept_ids if in_degree[cid] == 0])

        while queue:
            node = queue.popleft()
            topo_order.append(node)

            for neighbor in adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

    return {
        "concept_index": concept_index,
        "index_concept": index_concept,
        "concepts": concepts,   # ✅ Important addition
        "edges": valid_edges,
        "adjacency": dict(adjacency),
        "reverse_adjacency": dict(reverse_adjacency),
        "matrix": matrix,
        "is_dag": is_dag,
        "topological_order": topo_order,
        "cycles": cycles
    }


# =========================================================
# C) Unlock + Blocked Reasons (XAI Safe Version)
# =========================================================

def compute_unlocked_and_blocked(concepts: Dict[str, dict],
                                 reverse_adjacency: dict,
                                 mastery: Dict[str, float],
                                 threshold: float = 0.7) -> dict:
    """
    Returns:
        {
            "unlocked": [...],
            "blocked": [
                {
                    "concept_id": "P3",
                    "blocked_by": ["P2"],
                    "prereq_mastery": {"P2": 0.40},
                    "threshold": 0.70
                }
            ]
        }
    """

    unlocked = []
    blocked = []

    # ✅ FIX: include ALL concepts safely
    all_concepts = (
        set(concepts.keys())
        | set(reverse_adjacency.keys())
        | set(mastery.keys())
    )

    for concept in sorted(all_concepts):
        prereqs = reverse_adjacency.get(concept, [])

        # No prerequisites → unlocked
        if not prereqs:
            unlocked.append(concept)
            continue

        failed = []
        prereq_mastery = {}

        for p in prereqs:
            m = mastery.get(p, 0.0)
            prereq_mastery[p] = m
            if m < threshold:
                failed.append(p)

        if not failed:
            unlocked.append(concept)
        else:
            blocked.append({
                "concept_id": concept,
                "blocked_by": failed,
                "prereq_mastery": prereq_mastery,
                "threshold": threshold
            })

    return {
        "unlocked": unlocked,
        "blocked": blocked
    }


# =========================================================
# D) Entry Function
# =========================================================

def run_concept_dependency_module(db_paths: List[str]) -> dict:
    concepts, edges = load_concepts_and_edges(db_paths)
    return build_dependency_graph(concepts, edges)
