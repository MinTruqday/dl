export const questionTypes: string[]
export function moveItem<T>(values: T[], from: number, to: number): T[]
export function distributeDifficulty(total: number, preferred?: number): Record<string, number>
export function validDifficultyDistribution(total: number, distribution: Record<string, number>): boolean
export function remainingSeconds(expiresAt: string | null | undefined, currentTime?: number): number | null
export function formatDuration(seconds: number): string
