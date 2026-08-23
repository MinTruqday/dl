import test from "node:test"
import assert from "node:assert/strict"

import {
  distributeDifficulty,
  formatDuration,
  hasAnswerValue,
  moveItem,
  pendingResponseIds,
  remainingSeconds,
  validDifficultyDistribution,
} from "../lib/assessment.logic.mjs"


test("question order moves immutably", () => {
  const original = ["a", "b", "c"]
  assert.deepEqual(moveItem(original, 0, 2), ["b", "c", "a"])
  assert.deepEqual(original, ["a", "b", "c"])
})


test("five level blueprint validates exact total", () => {
  const distribution = distributeDifficulty(7, 4)
  assert.deepEqual(distribution, { "1": 0, "2": 0, "3": 0, "4": 7, "5": 0 })
  assert.equal(validDifficultyDistribution(7, distribution), true)
  assert.equal(validDifficultyDistribution(8, distribution), false)
})


test("timer is bounded and formatted", () => {
  assert.equal(remainingSeconds("2026-08-22T10:01:01Z", Date.parse("2026-08-22T10:00:00Z")), 61)
  assert.equal(remainingSeconds("2026-08-22T09:00:00Z", Date.parse("2026-08-22T10:00:00Z")), 0)
  assert.equal(formatDuration(3661), "01:01:01")
})


test("submit flushes every answered response not yet saved", () => {
  assert.deepEqual(
    pendingResponseIds({ q1: { option_id: "A" }, q2: { option_id: "B" }, q3: { value: 2 } }, { q1: true, q2: false }),
    ["q2", "q3"],
  )
})


test("answered state ignores blanks and preserves false and zero", () => {
  assert.equal(hasAnswerValue({ text: "   ", unit: "" }), false)
  assert.equal(hasAnswerValue({ value: false }), true)
  assert.equal(hasAnswerValue({ value: 0 }), true)
})
