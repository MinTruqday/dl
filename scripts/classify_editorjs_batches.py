import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "backend/compilation/src/resources/word-feature-manifest.json"
CAPABILITIES = ROOT / "backend/compilation/src/engines/editorjs_capabilities.py"


def load_verified():
    specification = importlib.util.spec_from_file_location("doclib_capabilities", CAPABILITIES)
    if specification is None or specification.loader is None:
        raise RuntimeError("Không thể nạp bộ khả năng")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    groups = (
        module.VERIFIED_PERSISTENT_COMMANDS,
        module.VERIFIED_STRUCTURE_COMMANDS,
        module.VERIFIED_TEXT_COMMANDS,
        module.VERIFIED_BLOCK_COMMANDS,
        module.VERIFIED_ANALYSIS_COMMANDS,
    )
    return set().union(*(group.keys() for group in groups))


def classify(feature, verified):
    command_id = feature["id"]
    if command_id in verified:
        status = "đã xác minh"
    elif feature.get("toolKey"):
        status = "chưa có bộ thực thi"
    else:
        status = "chỉ hiển thị"
    return {
        "id": command_id,
        "toolKey": feature.get("toolKey"),
        "mode": feature.get("mode"),
        "status": status,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument("--pending-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    features = json.loads(MANIFEST.read_text(encoding="utf-8"))["features"]
    verified = load_verified()
    if args.pending_only:
        features = [feature for feature in features if feature["id"] not in verified]
    batch = [classify(feature, verified) for feature in features[args.offset:args.offset + args.limit]]
    counts = Counter(item["status"] for item in batch)
    result = {
        "offset": args.offset,
        "limit": args.limit,
        "total": len(features),
        "batchCount": len(batch),
        "statusCounts": dict(counts),
        "items": batch,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"lô {args.offset // args.limit + 1} "
            f"vị trí {args.offset} đến {args.offset + len(batch) - 1} "
            f"đã xác minh {counts.get('đã xác minh', 0)} "
            f"chưa có bộ thực thi {counts.get('chưa có bộ thực thi', 0)} "
            f"chỉ hiển thị {counts.get('chỉ hiển thị', 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
