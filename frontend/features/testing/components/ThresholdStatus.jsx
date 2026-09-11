import { StatusPill } from "./WorkspacePrimitives";

const LOWER_IS_BETTER = new Set(["BLOCKED_RATE", "DEFECT_REOPEN_RATE", "CRITICAL_DEFECT_AGING", "MEAN_TIME_TO_RETEST", "STALE_TEST_RATIO", "REQUIREMENT_VOLATILITY", "ESCAPED_DEFECT_RATE"]);

export default function ThresholdStatus({ metricKey, value, target, warning, critical }) {
  let status = "NORMAL";
  if (LOWER_IS_BETTER.has(metricKey)) {
    if (critical !== null && critical !== undefined && value >= critical) status = "CRITICAL";
    else if (warning !== null && warning !== undefined && value >= warning) status = "WARNING";
    else if (target !== null && target !== undefined && value <= target) status = "TARGET_MET";
  } else {
    if (critical !== null && critical !== undefined && value <= critical) status = "CRITICAL";
    else if (warning !== null && warning !== undefined && value <= warning) status = "WARNING";
    else if (target !== null && target !== undefined && value >= target) status = "TARGET_MET";
  }
  return <StatusPill value={status} />;
}
