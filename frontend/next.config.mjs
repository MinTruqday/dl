import { PHASE_DEVELOPMENT_SERVER } from "next/constants.js";

export default function nextConfig(phase) {
  return {
    output: "standalone",
    distDir:
      phase === PHASE_DEVELOPMENT_SERVER
        ? process.env.NEXT_DIST_DIR || ".next-dev"
        : process.env.NEXT_BUILD_DIST_DIR || ".next",
  };
}
