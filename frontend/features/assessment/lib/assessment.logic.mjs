export const questionTypes = [
  "single_choice",
  "multiple_choice",
  "true_false",
  "matching",
  "ordering",
  "numeric",
  "symbolic_math",
  "short_answer",
  "essay",
]

export function moveItem(values, from, to) {
  if (from === to || from < 0 || to < 0 || from >= values.length || to >= values.length) return [...values]
  const result = [...values]
  const [item] = result.splice(from, 1)
  result.splice(to, 0, item)
  return result
}

export function distributeDifficulty(total, preferred = 3) {
  const result = { "1": 0, "2": 0, "3": 0, "4": 0, "5": 0 }
  result[String(Math.max(1, Math.min(5, preferred)))] = Math.max(0, total)
  return result
}

export function validDifficultyDistribution(total, distribution) {
  return ["1", "2", "3", "4", "5"].every((key) => Number.isInteger(distribution[key]) && distribution[key] >= 0)
    && Object.values(distribution).reduce((sum, value) => sum + value, 0) === total
}

export function remainingSeconds(expiresAt, currentTime = Date.now()) {
  if (!expiresAt) return null
  return Math.max(0, Math.ceil((new Date(expiresAt).getTime() - currentTime) / 1000))
}

export function formatDuration(seconds) {
  const value = Math.max(0, Number(seconds) || 0)
  const hours = Math.floor(value / 3600)
  const minutes = Math.floor((value % 3600) / 60)
  const remainder = value % 60
  return [hours, minutes, remainder].map((part) => String(part).padStart(2, "0")).join(":")
}

export function pendingResponseIds(answers, saved) {
  return Object.keys(answers).filter((questionVersionId) => !saved[questionVersionId])
}

export function hasAnswerValue(value) {
  if (typeof value === "string") return value.trim().length > 0
  if (Array.isArray(value)) return value.some(hasAnswerValue)
  if (value && typeof value === "object") return Object.values(value).some(hasAnswerValue)
  return value === false || value === 0 || Boolean(value)
}
