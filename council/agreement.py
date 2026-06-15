from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from itertools import combinations
import re

def extract_probability_range(text):

    if not text:
        return None

    text = str(text).lower()

    matches = re.findall(r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*%', text)

    if matches:
        low, high = matches[0]
        return float(low), float(high)

    percents = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)

    if percents:
        value = float(percents[0])
        return value, value

    return None


def probability_overlap_score(text_a, text_b):

    range_a = extract_probability_range(text_a)
    range_b = extract_probability_range(text_b)

    if not range_a or not range_b:
        return None

    a1, a2 = range_a
    b1, b2 = range_b

    overlap = max(0, min(a2, b2) - max(a1, b1))
    union = max(a2, b2) - min(a1, b1)

    if union <= 0:
        return 1.0

    return overlap / union

def normalize_confidence(value):

    if value is None:
        return 0.5

    if isinstance(value, (int, float)):
        confidence = float(value)
    else:
        text = str(value).lower()

        match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
        if match:
            confidence = float(match.group(1)) / 100
        else:
            try:
                confidence = float(text)
            except ValueError:
                if "very high" in text:
                    confidence = 0.95
                elif "high" in text:
                    confidence = 0.85
                elif "low-moderate" in text or "low moderate" in text:
                    confidence = 0.55
                elif "moderate" in text or "medium" in text:
                    confidence = 0.65
                elif "very low" in text:
                    confidence = 0.20
                elif "low" in text:
                    confidence = 0.35
                else:
                    confidence = 0.5

    if confidence > 1:
        confidence = confidence / 100

    return max(0.0, min(confidence, 1.0))


def extract_position_text(output):

    if output is None:
        return ""

    if isinstance(output, str):
        return output

    if not isinstance(output, dict):
        return str(output)

    for key in [
        "final_position",
        "proposed_answer",
        "answer",
        "final_answer",
        "position"
    ]:
        value = output.get(key)

        if value:
            return str(value)

    return str(output)

def extract_reasoning_text(output):

    if output is None:
        return ""

    if isinstance(output, str):
        return output

    if not isinstance(output, dict):
        return str(output)

    parts = []

    for key in [
        "final_position",
        "proposed_answer",
        "reasoning_summary",
        "change_reason",
        "feasibility_assessment",
        "technical_risks",
        "comments"
    ]:
        value = output.get(key)

        if value:
            if isinstance(value, list):
                parts.extend(str(v) for v in value)
            else:
                parts.append(str(value))

    return " ".join(parts)


def stance_direction(text):

    if not text:
        return 0

    text = str(text).lower()

    positive_patterns = [
        r"\byes\b",
        r"\bagree\b",
        r"\bsupport\b",
        r"\blikely\b",
        r"\bprobable\b",
        r"\bplausible\b",
        r"\bbeneficial\b",
        r"\brecommended\b",
        r"\bfavorable\b",
        r"\badvantageous\b",
        r"\bgood idea\b",
        r"\bworthwhile\b",
    ]

    negative_patterns = [
        r"\bno\b",
        r"\bdisagree\b",
        r"\boppose\b",
        r"\bunlikely\b",
        r"\bimprobable\b",
        r"\bunfavorable\b",
        r"\bnot recommended\b",
        r"\bpoor idea\b",
        r"\brisky\b",
        r"\bnot advisable\b",
        r"\bwill not\b",
        r"\bwon't\b",
    ]

    negative = sum(bool(re.search(p, text)) for p in negative_patterns)
    positive = sum(bool(re.search(p, text)) for p in positive_patterns)

    # AGI-specific special-case blocks removed
    # if re.search(r"unlikely.*before 2035", text):
    #     return -1
    #
    # if re.search(r"more likely.*after 2035", text):
    #     return -1
    #
    # if re.search(r"likely.*before 2035", text):
    #     return 1

    if positive > negative:
        return 1
    if negative > positive:
        return -1

    return 0


def cluster_answers(answers):

    texts = [extract_position_text(v) for v in answers.values()]

    if len(texts) < 2:
        return {"0": list(answers.keys())}

    directions = [stance_direction(t) for t in texts]

    positive = [a for a, d in zip(answers.keys(), directions) if d > 0]
    negative = [a for a, d in zip(answers.keys(), directions) if d < 0]
    neutral = [a for a, d in zip(answers.keys(), directions) if d == 0]

    clusters = {}

    if positive:
        clusters["1"] = positive

    if negative:
        clusters["-1"] = negative

    if neutral:
        clusters["0"] = neutral

    if len(clusters) == 1:
        return {"0": list(answers.keys())}

    return clusters


def semantic_agreement_score(answers):

    texts = [extract_reasoning_text(v) for v in answers.values() if v]

    if len(texts) < 2:
        return 1.0
    if len(set(t.strip().lower() for t in texts)) == 1:
        return 1.0

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(texts)

    similarity_matrix = cosine_similarity(X)

    n = len(texts)

    upper_triangle = [
        similarity_matrix[i][j]
        for i in range(n)
        for j in range(i + 1, n)
    ]

    if not upper_triangle:
        return 1.0

    return float(np.mean(upper_triangle))


def confidence_weighted_score(agent_outputs):

    if not agent_outputs:
        return 1.0

    confidences = []

    for output in agent_outputs.values():

        confidence = normalize_confidence(
            output.get("confidence", 0.5)
        )

        confidences.append(confidence)

    if not confidences:
        return 1.0

    return float(np.mean(confidences))


# Confidence alignment score
def confidence_alignment_score(agent_outputs):

    if not agent_outputs:
        return 1.0

    confidences = []

    for output in agent_outputs.values():
        confidences.append(
            normalize_confidence(
                output.get("confidence", 0.5)
            )
        )

    if len(confidences) < 2:
        return 1.0

    std = np.std(confidences)

    return max(0.0, 1.0 - std)


# Weighted semantic agreement function
def weighted_semantic_agreement(answers, agent_outputs):

    texts = [extract_reasoning_text(v) for v in answers.values() if v]
    agents = [k for k, v in answers.items() if v]

    if len(texts) < 2:
        return 1.0

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(texts)

    similarity_matrix = cosine_similarity(X)

    weighted_sum = 0.0
    weight_total = 0.0

    for i, j in combinations(range(len(agents)), 2):

        conf_a = normalize_confidence(
            agent_outputs.get(agents[i], {}).get("confidence", 0.5)
        )

        conf_b = normalize_confidence(
            agent_outputs.get(agents[j], {}).get("confidence", 0.5)
        )

        pair_weight = (conf_a + conf_b) / 2

        semantic_sim = similarity_matrix[i][j]

        position_a = extract_position_text(answers[agents[i]])
        position_b = extract_position_text(answers[agents[j]])

        stance_a = stance_direction(position_a)
        stance_b = stance_direction(position_b)

        if stance_a != 0 and stance_b != 0:
            if stance_a == stance_b:
                semantic_sim = max(semantic_sim, 0.80)
            else:
                semantic_sim = min(semantic_sim, 0.20)

        probability_sim = probability_overlap_score(
            position_a,
            position_b
        )

        if probability_sim is not None:
            semantic_sim = (
                0.5 * semantic_sim +
                0.5 * probability_sim
            )

        confidence_alignment = 1.0 - abs(conf_a - conf_b)

        semantic_sim = (
            0.55 * semantic_sim
            + 0.25 * confidence_alignment
            + 0.20 * (probability_sim if probability_sim is not None else semantic_sim)
        )

        weighted_sum += semantic_sim * pair_weight
        weight_total += pair_weight

    if weight_total == 0:
        return 1.0

    return float(weighted_sum / weight_total)
def pairwise_agreement_details(answers):

    texts = [extract_reasoning_text(v) for v in answers.values() if v]
    agents = [k for k, v in answers.items() if v]

    if len(texts) < 2:
        return {
            "average": 1.0,
            "pairs": []
        }

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(texts)

    similarity_matrix = cosine_similarity(X)

    pairs = []

    for i, j in combinations(range(len(agents)), 2):

        pos_a = extract_position_text(answers[agents[i]])
        pos_b = extract_position_text(answers[agents[j]])

        prob_overlap = probability_overlap_score(pos_a, pos_b)

        pairs.append({
            "agent_a": agents[i],
            "agent_b": agents[j],
            "similarity": round(float(similarity_matrix[i][j]), 3),
            "probability_overlap": round(float(prob_overlap), 3) if prob_overlap is not None else None,
            "stance_a": stance_direction(pos_a),
            "stance_b": stance_direction(pos_b)
        })

    average = np.mean([p["similarity"] for p in pairs])

    return {
        "average": round(float(average), 3),
        "pairs": pairs
    }


def stance_agreement_score(answers):

    directions = []

    for output in answers.values():
        direction = stance_direction(
            extract_position_text(output)
        )
        directions.append(direction)

    directions = [d for d in directions if d != 0]

    if len(directions) < 2:
        return 1.0

    same = 0
    total = 0

    for a, b in combinations(directions, 2):
        total += 1
        if a == b:
            same += 1

    return same / total if total else 1.0


def consensus_score(clusters, answers=None, agent_outputs=None):

    total = sum(len(v) for v in clusters.values())

    largest = max(len(v) for v in clusters.values())

    cluster_score = largest / total

    if answers is None and agent_outputs is None:
        return round(cluster_score, 3)

    semantic_score = (
        weighted_semantic_agreement(
            answers,
            agent_outputs or {}
        )
        if answers is not None
        else 1.0
    )
    stance_score = (
        stance_agreement_score(answers)
        if answers is not None
        else 1.0
    )

    confidence_score = (
        confidence_alignment_score(agent_outputs)
        if agent_outputs is not None
        else 1.0
    )

    final_score = (
        0.20 * cluster_score
        + 0.40 * semantic_score
        + 0.30 * stance_score
        + 0.10 * confidence_score
    )

    final_score = max(0.0, min(1.0, final_score))

    return round(final_score, 3)


def agreement_report(answers, agent_outputs):

    clusters = cluster_answers(answers)

    return {
        "clusters": clusters,
        "pairwise": pairwise_agreement_details(answers),
        "weighted_semantic": weighted_semantic_agreement(
            answers,
            agent_outputs
        ),
        "stance_agreement": stance_agreement_score(answers),
        "consensus": consensus_score(
            clusters,
            answers,
            agent_outputs
        )
    }