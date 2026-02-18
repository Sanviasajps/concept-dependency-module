import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple

from tutor.concept_dependency import (
    get_unlocked_concepts,
    get_blocked_concepts,
)

PREREQ_THRESHOLD = 0.60
MASTERY_TARGET = 0.80
ANOMALY_HIGH = 0.70

ALPHA = 0.65
BETA = 0.35

DIFFICULTY_ORDER = ["easy", "medium", "hard"]


# ============================================
# Utility: Check if table exists
# ============================================
def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        (table,),
    )
    return cursor.fetchone() is not None


# ============================================
# Step 1: Load Mastery (Correct Schema)
# ============================================
def load_latest_mastery(
    learner_id: str,
    conn: sqlite3.Connection,
) -> Dict[str, float]:

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT state_json
        FROM knowledge_state
        WHERE student_id = ?
        ORDER BY updated_at DESC
        LIMIT 1;
        """,
        (learner_id,),
    )

    row = cursor.fetchone()

    if not row or not row[0]:
        return {}

    try:
        full_state = json.loads(row[0])

        # Extract ONLY mastery dictionary
        mastery_section = full_state.get("mastery", {})

        if not isinstance(mastery_section, dict):
            return {}

        mastery = {}
        for concept_id, value in mastery_section.items():
            try:
                mastery[str(concept_id)] = float(value)
            except Exception:
                mastery[str(concept_id)] = 0.0

        return mastery

    except Exception:
        return {}


# ============================================
# Step 2: Load Behaviour (anomaly_score)
# ============================================
def load_latest_behavior(
    learner_id: str,
    conn: sqlite3.Connection,
) -> float:

    if not _table_exists(conn, "behaviour_state"):
        return 0.0

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT behavior_json
        FROM behaviour_state
        WHERE learner_id = ?
        ORDER BY timestamp DESC
        LIMIT 1;
        """,
        (learner_id,),
    )

    row = cursor.fetchone()

    if not row or not row[0]:
        return 0.0

    try:
        data = json.loads(row[0])
        if not isinstance(data, dict):
            return 0.0

        return float(data.get("anomaly_score", 0.0))

    except Exception:
        return 0.0


# ============================================
# Step 3: Load Decay
# ============================================
def load_latest_decay(
    learner_id: str,
    conn: sqlite3.Connection,
) -> Tuple[Dict[str, float], Dict[str, float]]:

    if not _table_exists(conn, "decay_state"):
        return {}, {}

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT decay_json, priority_json
        FROM decay_state
        WHERE learner_id = ?
        ORDER BY generated_at DESC
        LIMIT 1;
        """,
        (learner_id,),
    )

    row = cursor.fetchone()

    if not row:
        return {}, {}

    decay_json, priority_json = row

    try:
        decay_map = json.loads(decay_json) if decay_json else {}
        priority_map = json.loads(priority_json) if priority_json else {}

        if not isinstance(decay_map, dict):
            decay_map = {}

        if not isinstance(priority_map, dict):
            priority_map = {}

        decay_map = {str(k): float(v) for k, v in decay_map.items()}
        priority_map = {str(k): float(v) for k, v in priority_map.items()}

        return decay_map, priority_map

    except Exception:
        return {}, {}


# ============================================
# Mastery Gap
# ============================================
def _mastery_gap(mastery: float) -> float:
    return max(0.0, (MASTERY_TARGET - mastery) / MASTERY_TARGET)


# ============================================
# Choose Next Concept (Fusion)
# ============================================
def choose_next_concept(
    unlocked: List[str],
    mastery: Dict[str, float],
    priority: Dict[str, float],
) -> Tuple[Optional[str], List[dict]]:

    if not unlocked:
        return None, []

    scored = []

    for cid in unlocked:
        m = float(mastery.get(cid, 0.0))
        gap = _mastery_gap(m)
        pr = float(priority.get(cid, 0.0))

        score = ALPHA * gap + BETA * pr

        scored.append((cid, m, pr, score))

    scored.sort(key=lambda x: x[3], reverse=True)

    top_candidates = [
        {
            "concept_id": cid,
            "mastery": m,
            "priority": pr,
            "score": sc,
        }
        for cid, m, pr, sc in scored[:5]
    ]

    return scored[0][0], top_candidates


# ============================================
# Difficulty Selection
# ============================================
def choose_difficulty(
    concept_id: str,
    mastery: Dict[str, float],
    anomaly_score: float,
) -> str:

    m = float(mastery.get(concept_id, 0.0))

    if m < 0.60:
        base = "easy"
    elif m < 0.80:
        base = "medium"
    else:
        base = "hard"

    if anomaly_score >= ANOMALY_HIGH:
        idx = DIFFICULTY_ORDER.index(base)
        return DIFFICULTY_ORDER[max(0, idx - 1)]

    return base


# ============================================
# Main Function
# ============================================
def recommend_next_step(
    learner_id: str,
    tutor_conn: sqlite3.Connection,
    concept_db_paths: List[str],
) -> Dict[str, Any]:

    mastery_vec = load_latest_mastery(learner_id, tutor_conn)
    anomaly_score = load_latest_behavior(learner_id, tutor_conn)
    decay_map, priority_map = load_latest_decay(learner_id, tutor_conn)

    unlocked = get_unlocked_concepts(
        mastery_vec,
        PREREQ_THRESHOLD,
        concept_db_paths,
    )

    blocked = get_blocked_concepts(
        mastery_vec,
        PREREQ_THRESHOLD,
        concept_db_paths,
    )

    if not unlocked:
        return {
            "learner_id": learner_id,
            "next_concept_id": None,
            "difficulty": None,
            "reason": {
                "rule": "no_unlocked_concepts",
                "behavior_snapshot": {"anomaly_score": anomaly_score},
            },
            "unlocked_concepts": unlocked,
            "blocked_concepts": blocked,
        }

    next_id, top_candidates = choose_next_concept(
        unlocked,
        mastery_vec,
        priority_map,
    )

    difficulty = choose_difficulty(
        next_id,
        mastery_vec,
        anomaly_score,
    )

    return {
        "learner_id": learner_id,
        "next_concept_id": next_id,
        "difficulty": difficulty,
        "reason": {
            "rule": "priority_fusion_mastery_gap_plus_decay",
            "selected_mastery": float(mastery_vec.get(next_id, 0.0)),
            "selected_decay": float(decay_map.get(next_id, 0.0)),
            "selected_priority": float(priority_map.get(next_id, 0.0)),
            "thresholds": {
                "prereq_threshold": PREREQ_THRESHOLD,
                "mastery_target": MASTERY_TARGET,
                "anomaly_high": ANOMALY_HIGH,
                "alpha": ALPHA,
                "beta": BETA,
            },
            "behavior_snapshot": {"anomaly_score": anomaly_score},
            "candidate_pool": {
                "unlocked_count": len(unlocked),
                "blocked_count": len(blocked),
            },
            "top_candidates": top_candidates,
        },
        "unlocked_concepts": unlocked,
        "blocked_concepts": blocked,
    }
