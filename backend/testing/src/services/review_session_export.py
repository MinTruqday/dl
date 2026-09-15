import csv
import io
import json


def review_rows(review):
    values = [
        ("Mã phiên", review.get("review_key") or review.get("_id")),
        ("Dự án", review.get("project_id")),
        ("Loại rà soát", review.get("review_type")),
        ("Loại tài sản", review.get("artifact_type")),
        ("Mã tài sản", review.get("artifact_id")),
        ("Phiên bản tài sản", review.get("artifact_version_id")),
        ("Mục tiêu", review.get("objective")),
        ("Moderator", review.get("moderator_id")),
        ("Tác giả", review.get("author_id")),
        ("Reviewers", review.get("reviewer_ids", review.get("reviewers", []))),
        ("Scribe", review.get("scribe_id")),
        ("Trạng thái", review.get("status")),
        ("Quyết định", review.get("decision")),
        ("Số liệu", review.get("metrics", {})),
        ("Findings", review.get("findings", [])),
        ("Phiên nguồn", review.get("parent_review_session_id")),
        ("Bắt đầu", review.get("started_at")),
        ("Hoàn tất", review.get("completed_at")),
    ]
    return [
        (
            label,
            json.dumps(value, ensure_ascii=False, default=str)
            if isinstance(value, (dict, list))
            else str(value or ""),
        )
        for label, value in values
    ]


def export_review_csv(review):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Trường", "Giá trị"])
    writer.writerows(review_rows(review))
    return stream.getvalue().encode("utf-8-sig")
