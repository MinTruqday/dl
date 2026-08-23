from decimal import Decimal, InvalidOperation
import re
from statistics import median
from typing import Any
from urllib.parse import urlparse


ALLOWED_NODES = {
    "doc",
    "paragraph",
    "text",
    "heading",
    "bulletList",
    "orderedList",
    "listItem",
    "taskList",
    "taskItem",
    "blockquote",
    "codeBlock",
    "hardBreak",
    "horizontalRule",
    "image",
    "youtube",
    "details",
    "detailsSummary",
    "detailsContent",
    "table",
    "tableRow",
    "tableHeader",
    "tableCell",
    "inlineMath",
    "blockMath",
    "mathematics",
    "assessmentSection",
    "questionRef",
    "pageBreak",
}
ALLOWED_MARKS = {"bold", "italic", "strike", "code", "link", "underline", "subscript", "superscript", "highlight", "textStyle"}
ALLOWED_NODE_ATTRIBUTES = {
    "textAlign",
    "level",
    "src",
    "alt",
    "title",
    "width",
    "height",
    "colspan",
    "rowspan",
    "colwidth",
    "latex",
    "content",
    "sectionId",
    "questionId",
    "label",
    "language",
    "checked",
    "open",
    "start",
}
ALLOWED_MARK_ATTRIBUTES = {"href", "target", "rel", "class", "color", "fontFamily"}
ALLOWED_FONT_FAMILIES = {"Arial", "Georgia", "Times New Roman", "Courier New"}
SAFE_COLOR = re.compile(r"^(#[0-9a-fA-F]{3,8}|rgba?\([0-9.,% ]+\)|hsla?\([0-9.,% ]+\))$")
QUESTION_TYPES = {
    "single_choice",
    "multiple_choice",
    "true_false",
    "matching",
    "ordering",
    "numeric",
    "symbolic_math",
    "short_answer",
    "essay",
}


def finite_decimal(value: Any):
    if isinstance(value, bool) or value is None:
        return None
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return decimal if decimal.is_finite() else None


def validate_tiptap_content(node: Any):
    issues = []

    def visit(value: Any, path: str):
        if isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}.{index}")
            return
        if not isinstance(value, dict):
            return
        node_type = value.get("type")
        if node_type is not None and not isinstance(node_type, str):
            issues.append({"code": "invalid_tiptap_node_type", "severity": "BLOCKER", "path": path})
            node_type = None
        if node_type and node_type not in ALLOWED_NODES:
            issues.append({"code": "tiptap_node_not_allowed", "severity": "BLOCKER", "path": path, "node_type": node_type})
        marks = value.get("marks", [])
        if not isinstance(marks, list):
            issues.append({"code": "invalid_tiptap_marks", "severity": "BLOCKER", "path": path})
            marks = []
        for mark in marks:
            if not isinstance(mark, dict):
                issues.append({"code": "invalid_tiptap_mark", "severity": "BLOCKER", "path": path})
                continue
            if mark.get("type") not in ALLOWED_MARKS:
                issues.append({"code": "tiptap_mark_not_allowed", "severity": "BLOCKER", "path": path, "mark_type": mark.get("type")})
            mark_attrs = mark.get("attrs", {})
            if not isinstance(mark_attrs, dict):
                issues.append({"code": "invalid_tiptap_mark_attributes", "severity": "BLOCKER", "path": path})
                mark_attrs = {}
            if any(key not in ALLOWED_MARK_ATTRIBUTES for key in mark_attrs):
                issues.append({"code": "unsafe_tiptap_mark_attribute", "severity": "BLOCKER", "path": path})
            if mark.get("type") == "link":
                parsed_link = urlparse(str(mark_attrs.get("href", "")))
                if parsed_link.scheme not in {"https", "http", "mailto"}:
                    issues.append({"code": "link_url_not_allowed", "severity": "BLOCKER", "path": path})
            color = mark_attrs.get("color")
            if color is not None and not SAFE_COLOR.fullmatch(str(color)):
                issues.append({"code": "text_color_not_allowed", "severity": "BLOCKER", "path": path})
            font_family = mark_attrs.get("fontFamily")
            if font_family is not None and font_family not in ALLOWED_FONT_FAMILIES:
                issues.append({"code": "font_family_not_allowed", "severity": "BLOCKER", "path": path})
        attrs = value.get("attrs", {})
        if not isinstance(attrs, dict):
            issues.append({"code": "invalid_tiptap_attributes", "severity": "BLOCKER", "path": path})
            attrs = {}
        if any(key not in ALLOWED_NODE_ATTRIBUTES for key in attrs):
            issues.append({"code": "unsafe_tiptap_attribute", "severity": "BLOCKER", "path": path})
        if node_type == "image":
            source = str(attrs.get("src", ""))
            parsed = urlparse(source)
            if parsed.scheme not in {"https", "http"}:
                issues.append({"code": "image_url_not_allowed", "severity": "BLOCKER", "path": path})
            if not attrs.get("alt"):
                issues.append({"code": "image_alt_missing", "severity": "BLOCKER", "path": path})
        if node_type == "youtube":
            parsed_video = urlparse(str(attrs.get("src", "")))
            video_host = (parsed_video.hostname or "").casefold()
            if parsed_video.scheme != "https" or video_host not in {"youtube.com", "www.youtube.com", "youtu.be", "www.youtube-nocookie.com"}:
                issues.append({"code": "youtube_url_not_allowed", "severity": "BLOCKER", "path": path})
        if "textAlign" in attrs and attrs["textAlign"] not in {"left", "center", "right", "justify", None}:
            issues.append({"code": "text_alignment_not_allowed", "severity": "BLOCKER", "path": path})
        if node_type in {"inlineMath", "blockMath", "mathematics"}:
            latex = str(attrs.get("latex") or attrs.get("content") or "")
            if len(latex) > 10000 or any(token in latex for token in ["\\write", "\\input", "\\include", "\\openout"]):
                issues.append({"code": "unsafe_math_content", "severity": "BLOCKER", "path": path})
        for key, child in value.items():
            if key not in {"attrs", "marks"}:
                visit(child, f"{path}.{key}")

    visit(node, "doc")
    return issues


def text_parts(node: Any):
    values = []
    if isinstance(node, dict):
        if node.get("type") == "text" and isinstance(node.get("text"), str):
            values.append(node["text"])
        for key, value in node.items():
            if key == "text" and node.get("type") == "text":
                continue
            values.extend(text_parts(value))
    elif isinstance(node, list):
        for value in node:
            values.extend(text_parts(value))
    return values


def text_projection(node: Any):
    return " ".join(part.strip() for part in text_parts(node) if part.strip())


def normalized_tokens(node: Any):
    return {
        token.strip(".,:;!?()[]{}\"'").casefold()
        for token in text_projection(node).split()
        if token.strip(".,:;!?()[]{}\"'")
    }


def near_duplicate_score(left: dict[str, Any], right: dict[str, Any]):
    left_tokens = normalized_tokens(left.get("stem_doc", {}))
    right_tokens = normalized_tokens(right.get("stem_doc", {}))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens.intersection(right_tokens)) / len(left_tokens.union(right_tokens))


def validate_question(question: dict[str, Any]):
    checks = []
    blockers = []
    warnings = []
    stem = text_projection(question.get("stem_doc", {}))
    content_issues = validate_tiptap_content(question.get("stem_doc", {}))
    content_issues.extend(validate_tiptap_content(question.get("solution_doc", {})))
    for option in question.get("options", []):
        content_issues.extend(validate_tiptap_content(option.get("content_doc", {})))
    blockers.extend(issue for issue in content_issues if issue["severity"] == "BLOCKER")
    warnings.extend(issue for issue in content_issues if issue["severity"] == "WARNING")
    if not stem:
        blockers.append({"code": "missing_stem", "severity": "BLOCKER"})
    question_type = question.get("question_type")
    option_ids = [option.get("id") for option in question.get("options", [])]
    option_texts = [text_projection(option.get("content_doc", {})).casefold().strip() for option in question.get("options", [])]
    if question_type not in QUESTION_TYPES:
        blockers.append({"code": "invalid_question_type", "severity": "BLOCKER"})
    if any(not isinstance(option_id, str) or not option_id.strip() for option_id in option_ids):
        blockers.append({"code": "invalid_option_id", "severity": "BLOCKER"})
    if all(isinstance(option_id, str) for option_id in option_ids) and len(option_ids) != len(set(option_ids)):
        blockers.append({"code": "duplicate_option_id", "severity": "BLOCKER"})
    if len([text for text in option_texts if text]) != len(set(text for text in option_texts if text)):
        blockers.append({"code": "duplicate_option_content", "severity": "BLOCKER"})
    if question_type == "single_choice":
        key = question.get("answer_key", {}).get("option_id")
        if not key or key not in option_ids:
            blockers.append({"code": "invalid_answer_key", "severity": "BLOCKER"})
        if len(option_ids) < 2:
            blockers.append({"code": "insufficient_options", "severity": "BLOCKER"})
    if question_type == "multiple_choice":
        keys = question.get("answer_key", {}).get("option_ids", [])
        if (
            not isinstance(keys, list)
            or not keys
            or not all(isinstance(key, str) and key.strip() for key in keys)
            or len(keys) != len(set(keys))
            or any(key not in option_ids for key in keys)
        ):
            blockers.append({"code": "invalid_answer_key", "severity": "BLOCKER"})
        if len(option_ids) < 2:
            blockers.append({"code": "insufficient_options", "severity": "BLOCKER"})
    if question_type == "true_false":
        if not isinstance(question.get("answer_key", {}).get("value"), bool):
            blockers.append({"code": "invalid_answer_key", "severity": "BLOCKER"})
    if question_type == "matching":
        pairs = question.get("answer_key", {}).get("pairs", {})
        if (
            len(option_ids) < 2
            or not isinstance(pairs, dict)
            or set(pairs) != set(option_ids)
            or not all(isinstance(value, str) and value.strip() for value in pairs.values())
        ):
            blockers.append({"code": "invalid_matching_key", "severity": "BLOCKER"})
    if question_type == "ordering":
        order = question.get("answer_key", {}).get("order", [])
        if (
            len(option_ids) < 2
            or not isinstance(order, list)
            or not all(isinstance(key, str) and key.strip() for key in order)
            or len(order) != len(option_ids)
            or set(order) != set(option_ids)
        ):
            blockers.append({"code": "invalid_ordering_key", "severity": "BLOCKER"})
    if question_type == "numeric":
        answer_key = question.get("answer_key", {})
        value = finite_decimal(answer_key.get("value"))
        tolerance = finite_decimal(answer_key.get("tolerance", 0))
        if value is None:
            blockers.append({"code": "missing_numeric_answer", "severity": "BLOCKER"})
        if tolerance is None or tolerance < 0:
            blockers.append({"code": "invalid_numeric_tolerance", "severity": "BLOCKER"})
    if question_type in {"symbolic_math", "short_answer"}:
        accepted = question.get("answer_key", {}).get("accepted")
        if not isinstance(accepted, list) or not accepted or not all(isinstance(value, str) and value.strip() for value in accepted):
            blockers.append({"code": "invalid_accepted_answers", "severity": "BLOCKER"})
    if question_type in {"single_choice", "multiple_choice", "matching", "ordering"} and any(not text for text in option_texts):
        blockers.append({"code": "missing_option_content", "severity": "BLOCKER"})
    points = question.get("scoring_rule", {}).get("points")
    if not isinstance(points, (int, float)) or points <= 0:
        blockers.append({"code": "invalid_scoring_rule", "severity": "BLOCKER"})
    curriculum_links = question.get("curriculum_links") or []
    if not curriculum_links or any(not link.get("subject") or not link.get("target_program") for link in curriculum_links):
        blockers.append({"code": "missing_curriculum_mapping", "severity": "BLOCKER"})
    if not question.get("concept_ids") or not question.get("skill_ids"):
        blockers.append({"code": "missing_concept_skill_mapping", "severity": "BLOCKER"})
    construct = question.get("construct") or {}
    if any(not str(construct.get(key) or "").strip() for key in ["primary_concept", "primary_skill", "learning_objective"]):
        blockers.append({"code": "missing_construct", "severity": "BLOCKER"})
    issue_codes = {issue["code"] for issue in [*blockers, *warnings]}
    source_evidence = question.get("source_evidence", [])
    official_evidence = any(evidence.get("authority") in {"official", "verified"} for evidence in source_evidence)
    option_lengths = [len(text.split()) for text in option_texts if text]
    length_ratio = max(option_lengths) / max(1, min(option_lengths)) if option_lengths else 1
    answer_length_outlier = False
    if question_type == "single_choice" and option_lengths:
        key = question.get("answer_key", {}).get("option_id")
        keyed = [len(option_texts[index].split()) for index, option_id in enumerate(option_ids) if option_id == key]
        typical = median(option_lengths)
        answer_length_outlier = bool(keyed and typical and (keyed[0] > typical * 2 or keyed[0] * 2 < typical))
    generic_option_clue = any(
        phrase in text
        for text in option_texts
        for phrase in ("tất cả các đáp án", "cả ba đáp án", "không có đáp án nào", "all of the above", "none of the above")
    )
    distractor_plausible = question_type not in {"single_choice", "multiple_choice"} or (
        len(option_ids) >= 3 and length_ratio <= 4 and not generic_option_clue
    )
    clue_safe = question_type not in {"single_choice", "multiple_choice"} or (
        length_ratio <= 4 and not answer_length_outlier and not generic_option_clue
    )
    readability_safe = 4 <= len(stem.split()) <= 160
    essay_rubric = question.get("scoring_rule", {}).get("rubric")
    named_checks = [
        ("curriculum_alignment", "missing_curriculum_mapping" not in issue_codes, 0.9),
        ("concept_skill_alignment", "missing_construct" not in issue_codes and "missing_concept_skill_mapping" not in issue_codes, 0.75),
        ("factual_correctness", official_evidence, 0.7 if official_evidence else 0.35),
        ("answer_correctness", not any(code in issue_codes for code in {"invalid_answer_key", "missing_numeric_answer", "invalid_numeric_tolerance", "invalid_accepted_answers", "invalid_matching_key", "invalid_ordering_key"}), 1.0),
        ("ambiguity", len(stem.split()) >= 4, 0.55),
        ("duplicate_near_duplicate", "duplicate_option_content" not in issue_codes, 0.8),
        ("missing_information", bool(stem), 0.8),
        ("language_appropriateness", readability_safe, 0.65),
        ("cognitive_demand", bool(question.get("cognitive_level")), 0.7),
        ("question_type_validity", not any(code in issue_codes for code in {"invalid_question_type", "invalid_option_id", "insufficient_options", "invalid_answer_key", "invalid_matching_key", "invalid_ordering_key"}), 1.0),
        ("image_formula_integrity", not any(code in issue_codes for code in {"image_url_not_allowed", "unsafe_math_content"}), 0.95),
        ("scoring_validity", "invalid_scoring_rule" not in issue_codes, 1.0),
        ("construct_preservation", bool(question.get("construct")), 0.8),
        ("distractor_quality", distractor_plausible, 0.7),
        ("multiple_valid_answer_risk", question_type != "single_choice" or (question.get("answer_key", {}).get("option_id") in option_ids and len(set(option_texts)) == len(option_texts)), 0.8),
        ("clue_guessing_risk", clue_safe, 0.7),
        ("option_distribution", question_type not in {"single_choice", "multiple_choice"} or len(option_ids) >= 3, 0.65),
        ("essay_rubric_coverage", question_type != "essay" or bool(essay_rubric), 0.8),
        ("fairness_validity", (question.get("validity_review") or {}).get("status") not in {"pending", "rejected"}, 0.7),
    ]
    checks.extend(
        {
            "code": code,
            "status": "PASS" if passed else "NEEDS_REVIEW",
            "severity": "PASS" if passed else "NEEDS_REVIEW",
            "confidence": confidence,
        }
        for code, passed, confidence in named_checks
    )
    checks.extend(
        {
            **issue,
            "status": issue.get("status") or issue.get("severity", "BLOCKER"),
            "confidence": issue.get("confidence", 1.0),
        }
        for issue in [*blockers, *warnings]
    )
    named_review_required = any(not passed for _, passed, _ in named_checks)
    return {
        "status": "BLOCKER" if blockers else "NEEDS_REVIEW" if warnings or named_review_required else "PASS",
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "evidence": question.get("source_evidence", []),
        "confidence": 1.0,
        "plain_text_projection": stem,
    }
