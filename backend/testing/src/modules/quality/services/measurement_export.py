import csv
import io


def export_metric_csv(definition, snapshots):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(
        [
            "measurement_key",
            "definition_version",
            "release_id",
            "value",
            "unit",
            "dimensions",
            "source_fingerprint",
            "measured_at",
        ]
    )
    for item in snapshots:
        writer.writerow(
            [
                item.get("measurement_key", definition.get("key")),
                item.get("measurement_definition_version", definition.get("version")),
                item.get("release_id", ""),
                item.get("value", ""),
                item.get("unit", definition.get("unit", "")),
                str(item.get("dimensions", {})),
                item.get("source_fingerprint", ""),
                item.get("measured_at", ""),
            ]
        )
    return stream.getvalue().encode("utf-8-sig")
