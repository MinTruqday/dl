"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  getAssessmentAnalytics,
  getDifficultyComparison,
  getResearchEvaluation,
  getResearchMetrics,
  listAssessments,
} from "../services/assessment.service";
export default function CalibrationPage() {
  const searchParams = useSearchParams();
  const [assessmentId, setAssessmentId] = useState(searchParams.get("id") || "");
  const [assessments, setAssessments] = useState([]);
  const [data, setData] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    getResearchEvaluation()
      .then(setEvaluation)
      .catch((reason) =>
        setError(reason instanceof Error ? reason.message : "Không thể tải đánh giá nghiên cứu"),
      );
    listAssessments()
      .then((values) => {
        setAssessments(values);
        if (values[0]) setAssessmentId((current) => current || values[0]._id);
      })
      .catch((reason) =>
        setError(reason instanceof Error ? reason.message : "Không thể tải bài đánh giá"),
      );
  }, []);
  useEffect(() => {
    setMetrics(null);
    if (assessmentId) {
      Promise.all([getDifficultyComparison(assessmentId), getAssessmentAnalytics(assessmentId)])
        .then(([comparison, assessmentAnalytics]) => {
          setData(comparison);
          setAnalytics(assessmentAnalytics);
        })
        .catch((reason) =>
          setError(reason instanceof Error ? reason.message : "Không thể tải dữ liệu hiệu chỉnh"),
        );
    }
  }, [assessmentId]);
  const inspectMetrics = async (questionId) => {
    setError("");
    try {
      setMetrics(await getResearchMetrics(questionId));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tải chỉ số nghiên cứu");
    }
  };
  return (
    <div className="mx-auto max-w-[1400px] space-y-6 p-5 md:p-8">
      <div>
        <p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">
          Psychometrics
        </p>
        <h1 className="mt-2 text-[30px] font-semibold">Target và Teacher và AI và Empirical</h1>
      </div>
      <select
        className="apple-input max-w-xl"
        value={assessmentId}
        onChange={(event) => setAssessmentId(event.target.value)}
        aria-label="Chọn bài đánh giá"
      >
        <option value="">Chọn bài đánh giá</option>
        {assessments.map((assessment) => (
          <option key={assessment._id} value={assessment._id}>
            {assessment._id}
          </option>
        ))}
      </select>
      {analytics && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
            {[
              ["Attempts", analytics.attempts],
              [
                "Completion rate",
                `${Math.round(Number(analytics.completion_rate || 0) * 100)} phần trăm`,
              ],
              ["Điểm trung bình", analytics.average_score ?? "Chưa có"],
              ["Thời gian trung bình giây", analytics.average_completion_seconds ?? "Chưa có"],
              [
                "Câu có anomaly",
                (analytics.item_analysis || []).filter((item) => {
                  return item.anomaly_flags?.length;
                }).length,
              ],
            ].map(([label, value]) => (
              <div
                key={String(label)}
                className="rounded-panel border border-border bg-surface p-4"
              >
                <p className="text-[11px] uppercase text-ink-muted">{label}</p>
                <p className="mt-2 text-[22px] font-semibold">{value}</p>
              </div>
            ))}
          </div>
          <section className="rounded-panel border border-border bg-surface p-5">
            <h2 className="font-semibold">Phân bố điểm và hiệu quả theo topic</h2>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <pre className="overflow-auto whitespace-pre-wrap rounded-control bg-surface-quiet p-3 text-[12px]">
                {JSON.stringify(analytics.score_distribution, null, 2)}
              </pre>
              <div className="space-y-2">
                {(analytics.topic_performance || []).map((topic) => {
                  return (
                    <div
                      key={topic.topic}
                      className="rounded-control bg-surface-quiet p-3 text-[12px]"
                    >
                      <p className="font-semibold">{topic.topic}</p>
                      <p className="mt-1">
                        Accuracy {topic.accuracy ?? "Chưa có"} · Score rate{" "}
                        {topic.score_rate ?? "Chưa có"} · Response {topic.responses}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
          <section className="overflow-x-auto rounded-panel border border-border bg-surface">
            <table className="w-full min-w-[1500px] text-left text-[12px]">
              <thead className="bg-surface-quiet text-ink-muted">
                <tr>
                  <th className="p-4">Item</th>
                  <th className="p-4">Empirical</th>
                  <th className="p-4">Discrimination</th>
                  <th className="p-4">Distractors</th>
                  <th className="p-4">Omission</th>
                  <th className="p-4">Time ms</th>
                  <th className="p-4">Answer changes</th>
                  <th className="p-4">Fit</th>
                  <th className="p-4">Exposure</th>
                  <th className="p-4">Prediction error</th>
                  <th className="p-4">Anomaly</th>
                </tr>
              </thead>
              <tbody>
                {(analytics.item_analysis || []).map((item) => {
                  return (
                    <tr key={item.question_version_id} className="border-t border-border">
                      <td className="p-4 font-semibold">{item.question_version_id}</td>
                      <td className="p-4">{item.empirical ?? "Chưa có"}</td>
                      <td className="p-4">{item.discrimination ?? "Chưa có"}</td>
                      <td className="p-4 font-mono">
                        {JSON.stringify(item.distractor_distribution)}
                      </td>
                      <td className="p-4">{item.omission_count}</td>
                      <td className="p-4">{item.average_response_time_ms ?? "Chưa có"}</td>
                      <td className="p-4">{item.average_answer_changes}</td>
                      <td className="p-4">{item.item_fit_status ?? "Chưa có"}</td>
                      <td className="p-4">{item.exposure_count}</td>
                      <td className="p-4">{item.prediction_error ?? "Chưa có"}</td>
                      <td className="p-4">{item.anomaly_flags?.join(" · ") || "Không"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </section>
        </>
      )}
      {evaluation && (
        <section className="rounded-panel border border-border bg-surface p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-semibold">Đánh giá mô hình trên empirical calibration</h2>
              <p className="mt-1 text-[12px] text-ink-muted">
                Split theo logical question để tránh rò rỉ version
              </p>
            </div>
            <span
              className={`rounded-full px-3 py-1 text-[12px] font-semibold ${evaluation.leakage?.passed ? "bg-brand-soft text-brand" : "bg-danger-soft text-danger"}`}
            >
              {evaluation.leakage?.passed ? "Leakage check đạt" : "Có nguy cơ leakage"}
            </span>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {[
              ["Teacher baseline", evaluation.teacher],
              ["LLM direct judge", evaluation.llm_direct],
              ["Heuristic", evaluation.heuristic],
              ["Nearest historical", evaluation.nearest_historical],
              ["Structured AI", evaluation.structured],
              ["Teacher AI hybrid", evaluation.hybrid],
            ].map(([label, value]) => {
              return (
                <div key={label} className="rounded-control bg-surface-quiet p-4">
                  <p className="text-[11px] uppercase text-ink-muted">{label}</p>
                  <p className="mt-2 text-[13px]">
                    MAE <span className="font-semibold">{value?.mae ?? "Chưa đủ"}</span>
                  </p>
                  <p className="mt-1 text-[13px]">
                    RMSE <span className="font-semibold">{value?.rmse ?? "Chưa đủ"}</span>
                  </p>
                  <p className="mt-1 text-[13px]">
                    Spearman <span className="font-semibold">{value?.spearman ?? "Chưa đủ"}</span>
                  </p>
                  <p className="mt-1 text-[13px]">
                    Rank consistency{" "}
                    <span className="font-semibold">{value?.rank_consistency ?? "Chưa đủ"}</span>
                  </p>
                  <p className="mt-1 text-[13px]">
                    Uncertainty ECE{" "}
                    <span className="font-semibold">
                      {value?.uncertainty_calibration?.expected_calibration_error ?? "Chưa đủ"}
                    </span>
                  </p>
                  <p className="mt-1 text-[12px] text-ink-muted">N {value?.count || 0}</p>
                </div>
              );
            })}
          </div>
          <h3 className="mt-6 font-semibold">Độ ổn định theo cỡ mẫu</h3>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {(evaluation.calibration_stability || []).map((item) => {
              return (
                <div
                  key={item.question_version_id}
                  className="rounded-control border border-border p-4 text-[12px]"
                >
                  <p className="font-semibold">{item.question_version_id}</p>
                  <p className="mt-2">Cỡ mẫu mới nhất {item.latest_sample_size}</p>
                  <p>SE mới nhất {item.latest_standard_error ?? "Chưa đủ"}</p>
                  <p>Biên độ estimate {item.estimate_range ?? "Chưa đủ"}</p>
                  <p>
                    Ảnh hưởng lọc nhiễm bẩn{" "}
                    {item.latest_contamination_filter_difficulty_delta ?? "Chưa đủ"}
                  </p>
                  <p>Sample tăng đơn điệu {item.sample_size_monotonic ? "Có" : "Không"}</p>
                </div>
              );
            })}
          </div>
        </section>
      )}
      <section className="overflow-x-auto rounded-panel border border-border bg-surface">
        <table className="w-full min-w-[1200px] text-left text-[13px]">
          <thead className="bg-surface-quiet text-ink-muted">
            <tr>
              <th className="p-4">QuestionVersion</th>
              <th className="p-4">Target</th>
              <th className="p-4">Teacher</th>
              <th className="p-4">LLM direct</th>
              <th className="p-4">Structured AI</th>
              <th className="p-4">Empirical</th>
              <th className="p-4">Sample</th>
              <th className="p-4">SE</th>
              <th className="p-4">Nghiên cứu</th>
            </tr>
          </thead>
          <tbody>
            {(data?.items || []).map((row) => {
              const prompt = `Điều tra sai lệch độ khó của QuestionVersion ${row.question_version_id} bằng các công cụ miền Hãy lấy calibration đối chiếu Target Teacher AI Empirical kiểm tra curriculum và construct rồi chỉ tạo revision proposal có bằng chứng Không xuất bản hoặc sửa production`;
              return (
                <tr key={row.question_version_id} className="border-t border-border">
                  <td className="p-4 font-semibold">{row.question_version_id}</td>
                  <td className="p-4">{row.target ?? "Chưa có"}</td>
                  <td className="p-4">{row.teacher_estimate ?? "Chưa có"}</td>
                  <td className="p-4">{row.llm_direct_prediction ?? "Chưa có"}</td>
                  <td className="p-4">{row.ai_prediction ?? "Chưa có"}</td>
                  <td className="p-4">{row.empirical ?? "Chưa đủ dữ liệu"}</td>
                  <td className="p-4">{row.sample_size}</td>
                  <td className="p-4">{row.calibration_standard_error ?? "Chưa có"}</td>
                  <td className="p-4">
                    <div className="flex flex-col gap-2">
                      <button
                        type="button"
                        className="text-left font-semibold text-brand"
                        onClick={() => void inspectMetrics(row.question_id)}
                      >
                        So sánh v1 và v2
                      </button>
                      <Link
                        className="font-semibold text-brand"
                        href={`/tro-chuyen?mode=work&prompt=${encodeURIComponent(prompt)}`}
                      >
                        Agent điều tra sai lệch
                      </Link>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
      {metrics && (
        <section className="rounded-panel border border-border bg-surface p-5">
          <h2 className="font-semibold">Báo cáo hiệu quả sửa đổi</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-control bg-surface-quiet p-4">
              <p className="text-[11px] uppercase text-ink-muted">Error v1</p>
              <p className="mt-1 text-[24px] font-semibold">{metrics.error_v1 ?? "Chưa có"}</p>
            </div>
            <div className="rounded-control bg-surface-quiet p-4">
              <p className="text-[11px] uppercase text-ink-muted">Error v2</p>
              <p className="mt-1 text-[24px] font-semibold">{metrics.error_v2 ?? "Chưa có"}</p>
            </div>
            <div className="rounded-control bg-brand-soft p-4">
              <p className="text-[11px] uppercase text-ink-muted">Mức giảm sai số</p>
              <p className="mt-1 text-[24px] font-semibold">
                {metrics.error_reduction ?? "Chưa đủ dữ liệu"}
              </p>
            </div>
          </div>
        </section>
      )}
      {error && (
        <p role="alert" className="rounded-control bg-danger-soft p-3 text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
