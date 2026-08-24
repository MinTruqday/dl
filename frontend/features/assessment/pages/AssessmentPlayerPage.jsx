"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import TiptapReadOnly from "../editor/TiptapReadOnly";
import {
  createAttempt,
  getAssessmentPlayer,
  getAttempt,
  saveResponse,
  submitAttempt,
} from "../services/assessment.service";
import {
  formatDuration,
  hasAnswerValue,
  pendingResponseIds,
  remainingSeconds,
} from "../lib/assessment.logic.mjs";
export default function AssessmentPlayerPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const assessmentId = searchParams.get("id") || "";
  const assignmentId = searchParams.get("assignment") || "";
  const [player, setPlayer] = useState(null);
  const [attempt, setAttempt] = useState(null);
  const [position, setPosition] = useState(0);
  const [answers, setAnswers] = useState({});
  const [saved, setSaved] = useState({});
  const [flagged, setFlagged] = useState({});
  const [secondsLeft, setSecondsLeft] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const changes = useRef({});
  const questionStartedAt = useRef({});
  const pendingTechnicalFlags = useRef({});
  const answersRef = useRef({});
  const flaggedRef = useRef({});
  const saveTimers = useRef({});
  const submittedRef = useRef(false);
  const submitRef = useRef(null);
  const openingKeyRef = useRef("");
  useEffect(() => {
    if (!assessmentId) return;
    const openingKey = `${assessmentId}:${assignmentId || "direct"}`;
    if (openingKeyRef.current === openingKey) return;
    openingKeyRef.current = openingKey;
    const open = async () => {
      try {
        const [playerValue, attemptValue] = await Promise.all([
          getAssessmentPlayer(assessmentId, assignmentId),
          createAttempt(assessmentId, `attempt-${openingKey}`, assignmentId),
        ]);
        const resumed = await getAttempt(attemptValue._id);
        const existingAnswers = Object.fromEntries(
          (resumed.responses || []).map((response) => {
            const value = response;
            return [String(value.question_version_id), value.answer];
          }),
        );
        changes.current = Object.fromEntries(
          (resumed.responses || []).map((response) => {
            const value = response;
            return [String(value.question_version_id), Number(value.client_revision || 1)];
          }),
        );
        const existingFlags = Object.fromEntries(
          (resumed.responses || []).map((response) => {
            const value = response;
            return [String(value.question_version_id), Boolean(value.flag_for_review)];
          }),
        );
        answersRef.current = existingAnswers;
        flaggedRef.current = existingFlags;
        pendingTechnicalFlags.current = Object.fromEntries(
          Object.keys(existingAnswers).map((key) => [key, ["browser_reload"]]),
        );
        setPlayer(playerValue);
        setAttempt(resumed);
        setAnswers(existingAnswers);
        setFlagged(existingFlags);
        setSaved(Object.fromEntries(Object.keys(existingAnswers).map((key) => [key, true])));
        setSecondsLeft(remainingSeconds(resumed.expires_at));
      } catch (reason) {
        if (openingKeyRef.current === openingKey) openingKeyRef.current = "";
        setError(reason instanceof Error ? reason.message : "Không thể mở bài");
      }
    };
    void open();
  }, [assessmentId, assignmentId]);
  const persistResponse = async (
    questionVersionId,
    value,
    flagForReview,
    responseSequence,
    revision,
  ) => {
    if (!attempt) return;
    try {
      await saveResponse(attempt._id, {
        question_version_id: questionVersionId,
        answer: value,
        response_sequence: responseSequence,
        client_revision: Math.max(1, revision),
        response_time_ms: Date.now() - (questionStartedAt.current[questionVersionId] || Date.now()),
        answer_change_count: Math.max(0, revision - 1),
        is_first_exposure: true,
        exposure_index: 1,
        delivery_context: "assigned",
        technical_flags: pendingTechnicalFlags.current[questionVersionId] || [],
        flag_for_review: flagForReview,
        idempotency_key: `response-${attempt._id}-${questionVersionId}-${revision}`,
      });
      pendingTechnicalFlags.current[questionVersionId] = [];
      if (changes.current[questionVersionId] === revision) {
        setSaved((current) => ({
          ...current,
          [questionVersionId]: true,
        }));
      }
    } catch (reason) {
      pendingTechnicalFlags.current[questionVersionId] = ["network_error"];
      const failure = reason;
      setError(failure.message || "Không thể tự động lưu");
      if (failure.detail?.code === "attempt_time_expired") void submit(false);
      throw reason;
    }
  };
  const queueResponseSave = (
    questionVersionId,
    value,
    flagForReview,
    responseSequence,
    revision,
  ) => {
    window.clearTimeout(saveTimers.current[questionVersionId]);
    saveTimers.current[questionVersionId] = window.setTimeout(() => {
      delete saveTimers.current[questionVersionId];
      void persistResponse(
        questionVersionId,
        value,
        flagForReview,
        responseSequence,
        revision,
      ).catch(() => undefined);
    }, 700);
  };
  const submit = async (confirmIncomplete = true) => {
    if (!attempt || !player || submittedRef.current) return;
    if (
      confirmIncomplete &&
      answeredCount < player.items.length &&
      !window.confirm("Vẫn còn câu chưa trả lời bạn có muốn nộp bài")
    )
      return;
    submittedRef.current = true;
    setSubmitting(true);
    try {
      Object.values(saveTimers.current).forEach((timer) => window.clearTimeout(timer));
      saveTimers.current = {};
      const expired = attempt.expires_at ? remainingSeconds(attempt.expires_at) === 0 : false;
      if (!expired) {
        await Promise.all(
          pendingResponseIds(answersRef.current, saved).map((questionVersionId) => {
            const value = answersRef.current[questionVersionId];
            const responseSequence =
              player.items.findIndex((entry) => entry.question_version_id === questionVersionId) +
              1;
            return persistResponse(
              questionVersionId,
              value,
              Boolean(flaggedRef.current[questionVersionId]),
              Math.max(1, responseSequence),
              Math.max(1, changes.current[questionVersionId] || 1),
            );
          }),
        );
      }
      await submitAttempt(attempt._id);
      router.push(`/hoc-sinh/ket-qua?id=${attempt._id}`);
    } catch (reason) {
      submittedRef.current = false;
      setSubmitting(false);
      setError(reason instanceof Error ? reason.message : "Không thể nộp bài");
    }
  };
  submitRef.current = submit;
  useEffect(() => {
    if (!attempt?.expires_at) return;
    const tick = () => {
      const remaining = remainingSeconds(attempt.expires_at);
      setSecondsLeft(remaining);
      if (remaining === 0) void submitRef.current(false);
    };
    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [attempt?.expires_at, player, answers]);
  const item = player?.items[position];
  useEffect(() => {
    const recordVisibility = () => {
      if (document.visibilityState !== "hidden") return;
      const questionVersionId = player?.items[position]?.question_version_id;
      if (!questionVersionId) return;
      pendingTechnicalFlags.current[questionVersionId] = Array.from(
        new Set([...(pendingTechnicalFlags.current[questionVersionId] || []), "visibility_hidden"]),
      );
    };
    document.addEventListener("visibilitychange", recordVisibility);
    return () => document.removeEventListener("visibilitychange", recordVisibility);
  }, [player, position]);
  if (item && !questionStartedAt.current[item.question_version_id]) {
    questionStartedAt.current[item.question_version_id] = Date.now();
  }
  const answer = item ? answers[item.question_version_id] || {} : {};
  const answeredCount = useMemo(
    () => Object.values(answers).filter(hasAnswerValue).length,
    [answers],
  );
  const updateAnswer = (questionVersionId, value) => {
    const revision = (changes.current[questionVersionId] || 0) + 1;
    changes.current[questionVersionId] = revision;
    answersRef.current = {
      ...answersRef.current,
      [questionVersionId]: value,
    };
    setAnswers((current) => ({
      ...current,
      [questionVersionId]: value,
    }));
    setSaved((current) => ({
      ...current,
      [questionVersionId]: false,
    }));
    const responseSequence =
      (player?.items.findIndex((entry) => entry.question_version_id === questionVersionId) ?? -1) +
      1;
    queueResponseSave(
      questionVersionId,
      value,
      Boolean(flaggedRef.current[questionVersionId]),
      Math.max(1, responseSequence),
      revision,
    );
  };
  const updateFlag = (questionVersionId, value) => {
    flaggedRef.current = {
      ...flaggedRef.current,
      [questionVersionId]: value,
    };
    setFlagged((current) => ({
      ...current,
      [questionVersionId]: value,
    }));
    const currentAnswer = answersRef.current[questionVersionId];
    if (!currentAnswer) return;
    const revision = (changes.current[questionVersionId] || 0) + 1;
    changes.current[questionVersionId] = revision;
    setSaved((current) => ({
      ...current,
      [questionVersionId]: false,
    }));
    const responseSequence =
      (player?.items.findIndex((entry) => entry.question_version_id === questionVersionId) ?? -1) +
      1;
    queueResponseSave(
      questionVersionId,
      currentAnswer,
      value,
      Math.max(1, responseSequence),
      revision,
    );
  };
  useEffect(
    () => () => {
      Object.values(saveTimers.current).forEach((timer) => window.clearTimeout(timer));
    },
    [],
  );
  if (!assessmentId)
    return (
      <div role="alert" className="mx-auto max-w-4xl space-y-4 p-10 text-center">
        <p className="text-danger">Chưa chọn bài đánh giá</p>
        <button className="apple-button" onClick={() => router.push("/hoc-sinh/bai-duoc-giao")}>
          Quay lại bài được giao
        </button>
      </div>
    );
  if (error && (!player || !attempt))
    return (
      <div role="alert" className="mx-auto max-w-4xl p-10 text-center text-danger">
        {error}
      </div>
    );
  if (!player || !attempt || !item)
    return (
      <div className="mx-auto max-w-4xl p-10 text-center text-ink-muted">
        Đang mở phiên làm bài cố định
      </div>
    );
  const linear = player.delivery_policy.navigation === "linear";
  const optionOrder = answer.order || [];
  return (
    <div className="min-h-[calc(100dvh-60px)] bg-canvas">
      <header className="sticky top-[60px] z-20 border-b border-border bg-surface px-5 py-3">
        <div className="mx-auto flex max-w-[1300px] items-center gap-4">
          <div className="min-w-0 flex-1">
            <h1 className="truncate font-semibold">{player.title}</h1>
            <p className="text-[11px] text-ink-muted">{player.assessment_version_id}</p>
          </div>
          {secondsLeft !== null && (
            <span
              className={`font-mono text-[14px] font-semibold ${secondsLeft < 60 ? "text-danger" : ""}`}
              aria-live="polite"
              aria-label="Thời gian còn lại"
            >
              {formatDuration(secondsLeft)}
            </span>
          )}
          <span className="text-[13px]">
            Đã trả lời {answeredCount} trên {player.items.length}
          </span>
          <button className="apple-button" disabled={submitting} onClick={() => void submit()}>
            {submitting ? "Đang nộp" : "Nộp bài"}
          </button>
        </div>
      </header>
      <div className="mx-auto grid max-w-[1300px] gap-5 p-5 lg:grid-cols-[220px_minmax(0,1fr)]">
        <nav
          aria-label="Điều hướng câu hỏi"
          className="rounded-panel border border-border bg-surface p-4 lg:sticky lg:top-[130px] lg:self-start"
        >
          <p className="mb-3 text-[12px] font-semibold text-ink-muted">Điều hướng câu hỏi</p>
          <div className="grid grid-cols-5 gap-2 lg:grid-cols-4">
            {player.items.map((current, index) => (
              <button
                key={current.question_version_id}
                disabled={linear && index > position}
                aria-label={`Mở câu ${index + 1}`}
                className={`min-h-10 rounded-control border text-[13px] font-semibold ${index === position ? "border-brand bg-brand text-white" : hasAnswerValue(answers[current.question_version_id]) ? "border-brand bg-brand-soft text-brand" : flagged[current.question_version_id] ? "border-warning bg-warning-soft" : "border-border"}`}
                onClick={() => setPosition(index)}
              >
                {index + 1}
              </button>
            ))}
          </div>
        </nav>
        <div className="rounded-panel border border-border bg-surface p-5 md:p-8">
          <div className="flex items-center justify-between border-b border-border pb-4">
            <h2 className="text-[18px] font-semibold">Câu {position + 1}</h2>
            <div className="flex items-center gap-3">
              {Boolean(player.delivery_policy.allow_review_flags) && (
                <label className="text-[12px] text-ink-muted">
                  <input
                    type="checkbox"
                    checked={Boolean(flagged[item.question_version_id])}
                    onChange={(event) => updateFlag(item.question_version_id, event.target.checked)}
                  />{" "}
                  Đánh dấu xem lại
                </label>
              )}
              <span className="text-[12px] text-ink-muted">
                {hasAnswerValue(answers[item.question_version_id])
                  ? saved[item.question_version_id]
                    ? "Đã tự động lưu"
                    : "Đang lưu"
                  : "Chưa trả lời"}
              </span>
            </div>
          </div>
          <div className="py-6">
            <TiptapReadOnly value={item.question.stem_doc} label={`Nội dung câu ${position + 1}`} />
          </div>
          {["single_choice", "multiple_choice"].includes(item.question.question_type) && (
            <div className="space-y-3">
              {item.question.options.map((option) => {
                const selected =
                  item.question.question_type === "single_choice"
                    ? answer.option_id === option.id
                    : (answer.option_ids || []).includes(option.id);
                return (
                  <button
                    key={option.id}
                    aria-pressed={selected}
                    className={`flex w-full items-center gap-4 rounded-control border p-4 text-left ${selected ? "border-brand bg-brand-soft" : "border-border"}`}
                    onClick={() => {
                      if (item.question.question_type === "single_choice")
                        updateAnswer(item.question_version_id, { option_id: option.id });
                      else {
                        const current = answer.option_ids || [];
                        updateAnswer(item.question_version_id, {
                          option_ids: selected
                            ? current.filter((id) => id !== option.id)
                            : [...current, option.id],
                        });
                      }
                    }}
                  >
                    <span className="flex h-8 w-8 items-center justify-center rounded-full border border-current font-semibold">
                      {option.id}
                    </span>
                    <TiptapReadOnly value={option.content_doc} label={`Phương án ${option.id}`} />
                  </button>
                );
              })}
            </div>
          )}
          {item.question.question_type === "true_false" && (
            <div className="grid grid-cols-2 gap-3">
              <button
                aria-pressed={answer.value === true}
                className={`apple-button-secondary ${answer.value === true ? "border-brand bg-brand-soft" : ""}`}
                onClick={() => updateAnswer(item.question_version_id, { value: true })}
              >
                Đúng
              </button>
              <button
                aria-pressed={answer.value === false}
                className={`apple-button-secondary ${answer.value === false ? "border-brand bg-brand-soft" : ""}`}
                onClick={() => updateAnswer(item.question_version_id, { value: false })}
              >
                Sai
              </button>
            </div>
          )}
          {item.question.question_type === "numeric" && (
            <div className="grid gap-3 sm:grid-cols-[1fr_180px]">
              <input
                className="apple-input w-full"
                inputMode="decimal"
                value={String(answer.value ?? "")}
                onChange={(event) =>
                  updateAnswer(item.question_version_id, {
                    ...answer,
                    value: event.target.value,
                  })
                }
                aria-label="Câu trả lời số"
              />
              <input
                className="apple-input w-full"
                value={String(answer.unit ?? "")}
                onChange={(event) =>
                  updateAnswer(item.question_version_id, {
                    ...answer,
                    unit: event.target.value,
                  })
                }
                aria-label="Đơn vị"
                placeholder="Đơn vị"
              />
            </div>
          )}
          {item.question.question_type === "matching" && (
            <div className="space-y-2">
              {item.question.options.map((option) => {
                return (
                  <label
                    key={option.id}
                    className="grid items-center gap-3 rounded-control border border-border p-3 sm:grid-cols-[1fr_180px]"
                  >
                    <TiptapReadOnly value={option.content_doc} label={`Vế ghép ${option.id}`} />
                    <input
                      className="apple-input"
                      value={String(answer.pairs?.[option.id] || "")}
                      onChange={(event) =>
                        updateAnswer(item.question_version_id, {
                          pairs: {
                            ...(answer.pairs || {}),
                            [option.id]: event.target.value,
                          },
                        })
                      }
                      aria-label={`Câu ghép ${option.id}`}
                    />
                  </label>
                );
              })}
            </div>
          )}
          {item.question.question_type === "ordering" && (
            <div>
              <div className="flex flex-wrap gap-2">
                {item.question.options.map((option) => (
                  <button
                    key={option.id}
                    disabled={optionOrder.includes(option.id)}
                    className="apple-button-secondary"
                    onClick={() =>
                      updateAnswer(item.question_version_id, { order: [...optionOrder, option.id] })
                    }
                  >
                    {option.id}
                  </button>
                ))}
              </div>
              <p className="mt-3 text-[13px]">
                Thứ tự đã chọn {optionOrder.join(" → ") || "Chưa chọn"}
              </p>
              <button
                className="mt-2 text-[12px] text-brand"
                onClick={() => updateAnswer(item.question_version_id, { order: [] })}
              >
                Chọn lại
              </button>
            </div>
          )}
          {["short_answer", "essay", "symbolic_math"].includes(item.question.question_type) && (
            <textarea
              className="apple-input min-h-32 w-full"
              value={String(answer.text || "")}
              onChange={(event) =>
                updateAnswer(item.question_version_id, { text: event.target.value })
              }
              aria-label="Câu trả lời"
            />
          )}
          <div className="mt-8 flex justify-between">
            <button
              className="apple-button-secondary"
              disabled={position === 0 || linear}
              onClick={() => setPosition((current) => current - 1)}
            >
              Câu trước
            </button>
            <button
              className="apple-button"
              disabled={position === player.items.length - 1}
              onClick={() => setPosition((current) => current + 1)}
            >
              Câu sau
            </button>
          </div>
          {error && (
            <p role="alert" className="mt-4 rounded-control bg-danger-soft p-3 text-danger">
              {error}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
