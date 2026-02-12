# dependency_matrix.py

# --------------------------------------------------
# Get prerequisites of a concept
# --------------------------------------------------
def get_prereqs(concept_id, conn) -> list:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT prerequisite_id
        FROM concept_dependencies
        WHERE concept_id = ?
    """, (concept_id,))
    
    rows = cursor.fetchall()
    return [row[0] for row in rows]


# --------------------------------------------------
# Check if concept is unlocked
# --------------------------------------------------
def is_unlocked(concept_id, mastery_vector, threshold, conn) -> (bool, dict):
    prereqs = get_prereqs(concept_id, conn)

    # If no prerequisites → unlocked
    if not prereqs:
        return True, {}

    missing = []
    mastery_info = {}

    for p in prereqs:
        m = mastery_vector.get(p, 0.0)
        mastery_info[p] = m
        if m < threshold:
            missing.append(p)

    if not missing:
        return True, {}
    else:
        return False, {
            "concept_id": concept_id,
            "blocked_by": missing,
            "prereq_mastery": {k: mastery_info[k] for k in missing},
            "threshold": threshold
        }


# --------------------------------------------------
# Get all unlocked concepts
# --------------------------------------------------
def get_unlocked_concepts(mastery_vector, threshold, conn) -> list:
    cursor = conn.cursor()
    cursor.execute("SELECT concept_id FROM concepts;")
    concepts = [row[0] for row in cursor.fetchall()]

    unlocked = []

    for concept in concepts:
        status, _ = is_unlocked(concept, mastery_vector, threshold, conn)
        if status:
            unlocked.append(concept)

    return unlocked


# --------------------------------------------------
# Get all blocked concepts
# --------------------------------------------------
def get_blocked_concepts(mastery_vector, threshold, conn) -> list:
    cursor = conn.cursor()
    cursor.execute("SELECT concept_id FROM concepts;")
    concepts = [row[0] for row in cursor.fetchall()]

    blocked = []

    for concept in concepts:
        status, reason = is_unlocked(concept, mastery_vector, threshold, conn)
        if not status:
            blocked.append(reason)

    return blocked
