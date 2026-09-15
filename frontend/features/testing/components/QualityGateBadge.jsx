import { StatusPill } from "./WorkspacePrimitives";

export default function QualityGateBadge({ status }) {
  return <StatusPill value={status || "NOT_CONFIGURED"} />;
}
