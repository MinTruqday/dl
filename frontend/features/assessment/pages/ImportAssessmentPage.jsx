"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useSearchParams } from "next/navigation";
import { assessmentRequest, listAssessmentDrafts } from "../services/assessment.service";
function stemText(candidate) {
    var _a, _b, _c, _d;
    return ((_d = (_c = (_b = (_a = candidate.stem_doc) === null || _a === void 0 ? void 0 : _a.content) === null || _b === void 0 ? void 0 : _b[0]) === null || _c === void 0 ? void 0 : _c.content) === null || _d === void 0 ? void 0 : _d.map((node) => node.text || "").join("")) || "";
}
export default function ImportAssessmentPage() {
    const requestedId = useSearchParams().get("id") || "";
    const [drafts, setDrafts] = useState([]);
    const [draftId, setDraftId] = useState("");
    const [file, setFile] = useState(null);
    const [job, setJob] = useState(null);
    const [status, setStatus] = useState("");
    const [selected, setSelected] = useState({});
    const [corrections, setCorrections] = useState({});
    const [originalCandidates, setOriginalCandidates] = useState(null);
    const [previewUrl, setPreviewUrl] = useState("");
    useEffect(() => {
        listAssessmentDrafts().then((values) => {
            setDrafts(values);
            if (requestedId || values[0])
                setDraftId(requestedId || values[0]._id);
        });
    }, [requestedId]);
    useEffect(() => () => {
        if (previewUrl)
            URL.revokeObjectURL(previewUrl);
    }, [previewUrl]);
    const setCandidates = (candidates) => {
        setSelected(Object.fromEntries(candidates.map((candidate) => [candidate.candidate_id, Boolean(candidate.recognized)])));
        setCorrections(Object.fromEntries(candidates.map((candidate) => [candidate.candidate_id, stemText(candidate)])));
    };
    const parse = async () => {
        if (!file || !draftId)
            return;
        setStatus("Đang tải tệp");
        try {
            const data = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(String(reader.result || ""));
                reader.onerror = () => reject(new Error("Không thể đọc tệp"));
                reader.readAsDataURL(file);
            });
            setStatus("Đang OCR và tách câu hỏi");
            const value = await assessmentRequest(`/assessment-drafts/${draftId}/import-file`, {
                method: "POST",
                body: JSON.stringify({ idempotency_key: `import-${crypto.randomUUID()}`, file_name: file.name, data }),
            });
            setJob(value);
            setOriginalCandidates(structuredClone(value.candidates));
            setCandidates(value.candidates);
            setPreviewUrl(URL.createObjectURL(file));
            setStatus("Cần giáo viên rà soát");
        }
        catch (reason) {
            setStatus(reason instanceof Error ? reason.message : "Không thể phân tích tệp");
        }
    };
    const mergeNext = (index) => {
        var _a;
        if (!((_a = job === null || job === void 0 ? void 0 : job.candidates) === null || _a === void 0 ? void 0 : _a[index + 1]))
            return;
        const current = job.candidates[index];
        const next = job.candidates[index + 1];
        const candidates = job.candidates.filter((_, candidateIndex) => candidateIndex !== index + 1);
        setJob(Object.assign(Object.assign({}, job), { candidates }));
        setCorrections((values) => (Object.assign(Object.assign({}, values), { [current.candidate_id]: `${values[current.candidate_id] || ""}\n${values[next.candidate_id] || ""}`.trim() })));
        setSelected((values) => (Object.assign(Object.assign({}, values), { [next.candidate_id]: false })));
    };
    const splitCandidate = (index) => {
        var _a;
        if (!((_a = job === null || job === void 0 ? void 0 : job.candidates) === null || _a === void 0 ? void 0 : _a[index]))
            return;
        const candidate = job.candidates[index];
        const text = corrections[candidate.candidate_id] || "";
        const midpoint = text.indexOf("\n", Math.floor(text.length / 3));
        if (midpoint < 1) {
            setStatus("Cần có dòng mới để tách câu");
            return;
        }
        const first = text.slice(0, midpoint).trim();
        const second = text.slice(midpoint).trim();
        const derivedId = `${candidate.candidate_id}-split-${Date.now()}`;
        const derived = Object.assign(Object.assign({}, structuredClone(candidate)), { candidate_id: derivedId, stem_doc: { type: "doc", content: [{ type: "paragraph", content: [{ type: "text", text: second }] }] } });
        const candidates = [...job.candidates];
        candidates.splice(index + 1, 0, derived);
        setJob(Object.assign(Object.assign({}, job), { candidates }));
        setCorrections((values) => (Object.assign(Object.assign({}, values), { [candidate.candidate_id]: first, [derivedId]: second })));
        setSelected((values) => (Object.assign(Object.assign({}, values), { [derivedId]: true })));
    };
    const undoStructure = () => {
        if (!job || !originalCandidates)
            return;
        const candidates = structuredClone(originalCandidates);
        setJob(Object.assign(Object.assign({}, job), { candidates }));
        setCandidates(candidates);
    };
    const confirm = async () => {
        if (!job)
            return;
        const selectedCandidates = job.candidates.filter((candidate) => selected[candidate.candidate_id]);
        const correctedQuestions = Object.fromEntries(selectedCandidates.map((candidate) => [candidate.candidate_id, {
                question_type: candidate.question_type,
                authoring_source: "import",
                stem_doc: { type: "doc", content: corrections[candidate.candidate_id] ? [{ type: "paragraph", content: [{ type: "text", text: corrections[candidate.candidate_id] }] }] : [] },
                options: candidate.options,
                answer_key: candidate.answer_key,
                solution_doc: candidate.solution_doc,
                scoring_rule: candidate.scoring_rule,
                curriculum_links: candidate.curriculum_links,
                concept_ids: candidate.concept_ids,
                skill_ids: candidate.skill_ids,
                cognitive_level: candidate.cognitive_level,
                construct: candidate.construct,
                source_evidence: candidate.source_evidence,
                source_page: candidate.source_page,
                parse_confidence: candidate.parse_confidence,
                locked: false,
            }]));
        try {
            const value = await assessmentRequest(`/imports/${job._id}/confirm`, {
                method: "POST",
                body: JSON.stringify({ selected_candidate_ids: selectedCandidates.map((candidate) => candidate.candidate_id), corrected_questions: correctedQuestions }),
            });
            setJob(value);
            setStatus("Đã đưa vào AssessmentDraft");
        }
        catch (reason) {
            setStatus(reason instanceof Error ? reason.message : "Không thể xác nhận câu hỏi");
        }
    };
    return (<div className="mx-auto max-w-[1200px] space-y-6 p-5 md:p-8">
      <div><p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">Import Test</p><h1 className="mt-2 text-[30px] font-semibold">Nhập đề có sẵn</h1><p className="mt-2 text-[13px] text-ink-muted">PDF DOCX và hình ảnh đi qua Docling OCR trước khi giáo viên rà soát</p></div>
      <section className="grid gap-4 rounded-panel border border-border bg-surface p-5 md:grid-cols-2" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { var _a; event.preventDefault(); setFile(((_a = event.dataTransfer.files) === null || _a === void 0 ? void 0 : _a[0]) || null); }}>
        <label className="text-[13px] font-semibold">AssessmentDraft<select className="apple-input mt-2 w-full" value={draftId} onChange={(event) => setDraftId(event.target.value)}>{drafts.map((draft) => <option key={draft._id} value={draft._id}>{draft.title}</option>)}</select></label>
        <label className="text-[13px] font-semibold">Kéo thả hoặc chọn PDF DOCX hay hình ảnh<input className="apple-input mt-2 w-full" type="file" accept=".pdf,.docx,image/*" onChange={(event) => { var _a; return setFile(((_a = event.target.files) === null || _a === void 0 ? void 0 : _a[0]) || null); }}/></label>
        <p className="text-[12px] text-ink-muted md:col-span-2">{(file === null || file === void 0 ? void 0 : file.name) || "Chưa chọn tệp"}</p>
        <button className="apple-button md:col-span-2" disabled={!file || !draftId} onClick={parse}>Tách câu hỏi</button>
      </section>
      {(job === null || job === void 0 ? void 0 : job.candidates) && <section className="rounded-panel border border-border bg-surface">
        <div className="flex items-center justify-between border-b border-border px-5 py-4"><h2 className="font-semibold">Nguồn và câu hỏi đã nhận dạng</h2><span className="text-[12px] text-ink-muted">{status}</span></div>
        <div className="grid lg:grid-cols-[minmax(280px,0.8fr)_minmax(0,1.2fr)]">
          <aside className="border-b border-border p-4 lg:border-b-0 lg:border-r">{(file === null || file === void 0 ? void 0 : file.type.startsWith("image/")) && previewUrl ? <Image src={previewUrl} alt="Tệp nguồn đã tải lên" width={900} height={1200} unoptimized className="max-h-[70vh] w-full object-contain"/> : (file === null || file === void 0 ? void 0 : file.type) === "application/pdf" && previewUrl ? <iframe title="Tệp PDF nguồn" src={previewUrl} className="h-[70vh] w-full"/> : <div className="rounded-control bg-surface-quiet p-5 text-[13px]"><p className="font-semibold">{file === null || file === void 0 ? void 0 : file.name}</p><p className="mt-2 text-ink-muted">Đối chiếu số trang công thức và hình ảnh trong từng candidate</p></div>}</aside>
          <div className="divide-y divide-border">{job.candidates.map((candidate, index) => <div key={candidate.candidate_id} className="px-5 py-5">
            <label className="flex items-start gap-3 rounded-control bg-surface-quiet p-3 text-[13px]"><input type="checkbox" checked={Boolean(selected[candidate.candidate_id])} onChange={(event) => setSelected((current) => (Object.assign(Object.assign({}, current), { [candidate.candidate_id]: event.target.checked })))}/>Trang nguồn {candidate.source_page}</label>
            <p className="mt-3 font-semibold">{candidate.candidate_id}</p>
            <textarea className="apple-input mt-2 min-h-24 w-full" value={corrections[candidate.candidate_id] || ""} onChange={(event) => setCorrections((current) => (Object.assign(Object.assign({}, current), { [candidate.candidate_id]: event.target.value })))} aria-label={`Nội dung ${candidate.candidate_id}`}/>
            <div className="mt-2 flex flex-wrap gap-2"><button className="apple-button-secondary" onClick={() => mergeNext(index)} disabled={!job.candidates[index + 1]}>Ghép câu kế tiếp</button><button className="apple-button-secondary" onClick={() => splitCandidate(index)}>Tách tại dòng gần giữa</button></div>
            <p className="mt-2 text-[12px] text-ink-muted">Độ tin cậy {Math.round(candidate.parse_confidence * 100)} phần trăm {(candidate.exception_flags || []).join(" ") || "Không có cảnh báo"}</p>
          </div>)}</div>
        </div>
        <div className="flex justify-end gap-2 border-t border-border p-4"><button className="apple-button-secondary" onClick={undoStructure}>Hoàn tác cấu trúc</button><button className="apple-button" onClick={confirm}>Xác nhận câu đã chọn</button></div>
      </section>}
      {(job === null || job === void 0 ? void 0 : job.questions) && <Link className="apple-button" href={`/giao-vien/de/soan-thao?id=${draftId}`}>Mở trong Composer</Link>}
      {!(job === null || job === void 0 ? void 0 : job.candidates) && status && <p role="status" className="rounded-control bg-surface-quiet p-3 text-[13px]">{status}</p>}
    </div>);
}
