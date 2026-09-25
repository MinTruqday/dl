import { PHASE_DEVELOPMENT_SERVER } from "next/constants.js";

export default function nextConfig(phase) {
  const distDir =
    phase === PHASE_DEVELOPMENT_SERVER
      ? process.env.NEXT_DIST_DIR?.trim()
      : process.env.NEXT_BUILD_DIST_DIR?.trim();
  if (!distDir) throw new Error("Next.js distribution directory is required");
  return {
    output: "standalone",
    distDir,
  };
}
