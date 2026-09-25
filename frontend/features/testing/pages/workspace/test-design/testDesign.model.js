import { emptyDoc } from "../../../lib/testing";

export const TEST_CASE_TYPES = [
  "happy_path",
  "negative",
  "boundary",
  "validation",
  "permission",
  "state_transition",
  "integration",
  "error_handling",
  "data_persistence",
  "concurrency",
  "api",
  "ui",
  "custom",
];

export const TEST_SCENARIO_CATEGORIES = TEST_CASE_TYPES.filter(
  (value) => !["api", "ui", "custom"].includes(value),
);

export const TEST_LEVELS = ["critical", "high", "medium", "low"];

export const AI_TEST_GENERATION_CATEGORIES = ["happy_path", "negative", "boundary", "validation"];

export function createTestCaseForm() {
  return {
    title: "",
    type: "happy_path",
    priority: "medium",
    risk: "medium",
    action: emptyDoc(),
    expected: emptyDoc(),
    dataSetVersionIds: [],
    testConditionIds: [],
  };
}

export function createScenarioForm() {
  return {
    title: "",
    objective: "",
    category: "happy_path",
    testConditionIds: [],
  };
}

export function createDataSetForm() {
  return { name: "", variables: "{}", secretRefs: "{}" };
}

export function selectedValues(event) {
  return Array.from(event.target.selectedOptions, (option) => option.value);
}
