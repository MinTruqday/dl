"use client";

import { FormEvent, useEffect, useState } from "react";
import { uploadDocumentAPI } from "@/features/cloud/services/upload.service";
import { createDocumentAPI, deleteAuthorDocumentAPI, getDocumentDraftAPI, getMyDocumentsAPI, retryDocumentIndexingAPI, updateDocumentAPI } from "@/features/content/services/document.service";
import { createTeacherMaterialMapping, listSourceMappings, reviewSourceMapping, searchTeacherMaterials } from "@/features/assessment/services/assessment.service";

function slugOf(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "") || "tai-lieu-giao-vien";
}

function extensionOf(file: File) {
  const extension = file.name.split(".").pop()?.toLowerCase() || "txt";
  return extension === "md" ? "markdown" : extension === "tex" ? "latex" : extension;
}

async function sha256(file: File) {
  const bytes = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(bytes), (value) => value.toString(16).padStart(2, "0")).join("");
}

export default function TeacherMaterialPage() {
  const [materials, setMaterials] = useState<Record<string, any>[]>([]);
  const [mappings, setMappings] = useState<Record<string, Record<string, any>>>({});
  const [mappingConcepts, setMappingConcepts] = useState<Record<string, string>>({});
  const [mappingNodes, setMappingNodes] = useState<Record<string, string>>({});
  const [mappingSkills, setMappingSkills] = useState<Record<string, string>>({});
  const [title, setTitle] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [progress, setProgress] = useState(0);
  const [materialSearch, setMaterialSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("");
  const [topicFilter, setTopicFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [semanticResults, setSemanticResults] = useState<Record<string, any>[]>([]);
  const [semanticConflicts, setSemanticConflicts] = useState<Record<string, any>[]>([]);
  const [extractedText, setExtractedText] = useState<Record<string, string>>({});
  const [educationLevel, setEducationLevel] = useState("THPT");
  const [subject, setSubject] = useState("math");
  const [targetProgram, setTargetProgram] = useState("grade_12");
  const [chapterId, setChapterId] = useState("");
  const [lessonId, setLessonId] = useState("");
  const [conceptIds, setConceptIds] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    const response = await getMyDocumentsAPI("", "", 100);
    const rows = response.data ?? response ?? [];
    const teacherMaterials = rows.filter((row: any) => row.education_metadata?.source_type === "teacher_material");
    const mappingRows = await Promise.all(
      teacherMaterials.map(async (row: any) => [row._id, (await listSourceMappings(row._id))[0]] as const),
    );
    setMaterials(teacherMaterials);
    setMappings(Object.fromEntries(mappingRows.filter(([, mapping]) => mapping)));
    setMappingConcepts(Object.fromEntries(mappingRows.map(([documentId, mapping]) => [documentId, (mapping?.concept_ids || []).join(", ")])));
    setMappingNodes(Object.fromEntries(mappingRows.map(([documentId, mapping]) => [documentId, (mapping?.curriculum_node_ids || []).join(", ")])));
    setMappingSkills(Object.fromEntries(mappingRows.map(([documentId, mapping]) => [documentId, (mapping?.skill_ids || []).join(", ")])));
  };

  useEffect(() => {
    load().catch((reason) => setError(reason instanceof Error ? reason.message : "Không thể tải tài liệu giáo viên"));
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!files.length || !title.trim()) return;
    setBusy(true);
    setError("");
    setNotice("");
    setProgress(0);
    try {
      for (const [index, file] of files.entries()) {
        let documentId = "";
        try {
          const displayTitle = files.length === 1 ? title.trim() : `${title.trim()} ${file.name.replace(/\.[^.]+$/, "")}`;
          const created = await createDocumentAPI({
            title: displayTitle,
            slug: `${slugOf(displayTitle)}-${crypto.randomUUID().slice(0, 8)}`,
            description: "Tài liệu bổ trợ riêng của giáo viên",
            visibility: "private",
            category: "Teacher Material",
            content_format: "doclib",
          });
          documentId = created.data?._id ?? created.data?.id ?? created._id ?? created.id;
          const [uploaded, sourceVersion] = await Promise.all([uploadDocumentAPI(file), sha256(file)]);
          const fileUrl = uploaded.data?.url ?? uploaded.data?.file_path;
          if (!fileUrl) throw new Error("Không nhận được đường dẫn tệp đã tải lên");
          const concepts = conceptIds.split(/[,;\n]+/).map((value) => value.trim()).filter(Boolean);
          await updateDocumentAPI(documentId, {
            file_url: fileUrl,
            content_format: uploaded.data?.extension ?? extensionOf(file),
            education_metadata: {
              source_type: "teacher_material",
              authority: "supplementary",
              education_level: educationLevel,
              subject,
              target_program: targetProgram,
              chapter_id: chapterId || null,
              lesson_id: lessonId || null,
              concept_ids: concepts,
              skill_ids: [],
              learning_objective_ids: [],
              content_type: "teacher_material",
              source_version: sourceVersion,
              mapping_confidence: chapterId || lessonId || concepts.length ? 0.7 : 0.4,
              mapping_status: "needs_review",
            },
          });
          await createTeacherMaterialMapping(documentId, {
            chunk_id: `document-${documentId}`,
            curriculum_node_ids: [],
            concept_ids: concepts,
            skill_ids: [],
            mapping_confidence: chapterId || lessonId || concepts.length ? 0.7 : 0.4,
            mapping_status: "needs_review",
            source_version: sourceVersion,
          });
          setProgress(Math.round((index + 1) / files.length * 100));
        } catch (reason) {
          if (documentId) await deleteAuthorDocumentAPI(documentId).catch(() => undefined);
          throw reason;
        }
      }
      setTitle("");
      setFiles([]);
      setChapterId("");
      setLessonId("");
      setConceptIds("");
      setNotice(`Đã lưu ${files.length} tài liệu riêng và đưa vào hàng đợi lập chỉ mục`);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tải tài liệu giáo viên");
    } finally {
      setBusy(false);
    }
  };

  const renameMaterial = async (material: Record<string, any>) => {
    const nextTitle = window.prompt("Tên tài liệu mới", material.title || "");
    if (!nextTitle?.trim()) return;
    await updateDocumentAPI(material._id, { title: nextTitle.trim() });
    setNotice("Đã đổi tên tài liệu");
    await load();
  };

  const removeMaterial = async (materialId: string) => {
    if (!window.confirm("Xóa tài liệu riêng này")) return;
    await deleteAuthorDocumentAPI(materialId);
    setNotice("Đã chuyển tài liệu khỏi thư viện riêng");
    await load();
  };

  const replaceMaterialVersion = async (material: Record<string, any>, replacement: File) => {
    setBusy(true);
    setError("");
    try {
      const [uploaded, sourceVersion] = await Promise.all([uploadDocumentAPI(replacement), sha256(replacement)]);
      const fileUrl = uploaded.data?.url ?? uploaded.data?.file_path;
      if (!fileUrl) throw new Error("Không nhận được đường dẫn tệp đã tải lên");
      await updateDocumentAPI(material._id, {
        file_url: fileUrl,
        content_format: uploaded.data?.extension ?? extensionOf(replacement),
        education_metadata: { ...material.education_metadata, source_version: sourceVersion, mapping_status: "needs_review" },
      });
      const currentMapping = mappings[material._id];
      await createTeacherMaterialMapping(material._id, {
        chunk_id: `document-${material._id}-${sourceVersion.slice(0, 16)}`,
        curriculum_node_ids: currentMapping?.curriculum_node_ids || [],
        concept_ids: currentMapping?.concept_ids || [],
        skill_ids: currentMapping?.skill_ids || [],
        mapping_confidence: currentMapping?.mapping_confidence || 0.4,
        mapping_status: "needs_review",
        source_version: sourceVersion,
      });
      await retryDocumentIndexingAPI(material._id);
      setNotice("Đã tạo phiên bản nguồn mới và đưa vào hàng đợi lập chỉ mục lại");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể thay phiên bản tài liệu");
    } finally {
      setBusy(false);
    }
  };

  const visibleMaterials = materials.filter((material) => {
    const indexingStatus = material.indexing_status || (material.is_indexed ? "indexed" : "queued");
    const metadata = material.education_metadata || {};
    const materialDate = new Date(material.updated_at || material.created_at || 0).getTime();
    const topicText = [metadata.chapter_id, metadata.lesson_id, ...(metadata.concept_ids || []), ...(metadata.skill_ids || [])].join(" ").toLocaleLowerCase();
    return (!materialSearch || String(material.title || "").toLocaleLowerCase().includes(materialSearch.toLocaleLowerCase()))
      && (!statusFilter || indexingStatus === statusFilter)
      && (!subjectFilter || metadata.subject === subjectFilter)
      && (!topicFilter || topicText.includes(topicFilter.toLocaleLowerCase()))
      && (!typeFilter || material.content_format === typeFilter)
      && (!dateFrom || materialDate >= new Date(`${dateFrom}T00:00:00`).getTime())
      && (!dateTo || materialDate <= new Date(`${dateTo}T23:59:59.999`).getTime());
  });

  const searchIndexedContent = async () => {
    if (!materialSearch.trim()) return;
    setBusy(true);
    setError("");
    try {
      const result = await searchTeacherMaterials(materialSearch.trim(), subjectFilter);
      setSemanticResults(result.documents || []);
      setSemanticConflicts(result.conflicts || []);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tìm trong nội dung đã lập chỉ mục");
    } finally {
      setBusy(false);
    }
  };

  const reviewMapping = async (documentId: string, mappingStatus: "confirmed" | "needs_review") => {
    const mapping = mappings[documentId];
    if (!mapping) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const concepts = (mappingConcepts[documentId] || "").split(/[,;\n]+/).map((value) => value.trim()).filter(Boolean);
      const curriculumNodes = (mappingNodes[documentId] || "").split(/[,;\n]+/).map((value) => value.trim()).filter(Boolean);
      const skills = (mappingSkills[documentId] || "").split(/[,;\n]+/).map((value) => value.trim()).filter(Boolean);
      await reviewSourceMapping(documentId, mapping._id, {
        mapping_status: mappingStatus,
        mapping_confidence: mappingStatus === "confirmed" ? 1 : mapping.mapping_confidence,
        curriculum_node_ids: curriculumNodes,
        concept_ids: concepts,
        skill_ids: skills,
      });
      setNotice(mappingStatus === "confirmed" ? "Đã xác nhận ánh xạ tài liệu" : "Đã đưa ánh xạ về trạng thái cần rà soát");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể cập nhật ánh xạ tài liệu");
    } finally {
      setBusy(false);
    }
  };

  const retryIndexing = async (documentId: string) => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await retryDocumentIndexingAPI(documentId);
      setNotice("Đã đưa tài liệu vào hàng đợi lập chỉ mục");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể lập chỉ mục lại tài liệu");
    } finally {
      setBusy(false);
    }
  };

  const loadExtractedText = async (documentId: string) => {
    if (extractedText[documentId] !== undefined) {
      setExtractedText((current) => {
        const next = { ...current };
        delete next[documentId];
        return next;
      });
      return;
    }
    setBusy(true);
    setError("");
    try {
      const response = await getDocumentDraftAPI(documentId);
      const document = response.data ?? response;
      setExtractedText((current) => ({ ...current, [documentId]: String(document.extracted_text || "") }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tải văn bản đã trích xuất");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-[1200px] space-y-6 p-5 md:p-8">
      <div><p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">Teacher Material</p><h1 className="mt-2 text-[30px] font-semibold">Tài liệu bổ trợ riêng</h1><p className="mt-2 text-[13px] text-ink-muted">Tài liệu chỉ được truy xuất trong phạm vi chủ sở hữu và không thay thế curriculum chính thống</p></div>
      <form className="grid gap-4 rounded-panel border border-border bg-surface p-5 md:grid-cols-2" onSubmit={submit}>
        <label className="text-[13px] font-semibold">Tên tài liệu<input className="apple-input mt-2 w-full" value={title} onChange={(event) => setTitle(event.target.value)} required /></label>
        <label className="text-[13px] font-semibold">Tệp nguồn<input className="apple-input mt-2 w-full" type="file" multiple accept=".pdf,.docx,.pptx,.txt,.md,.tex,.png,.jpg,.jpeg,.webp" onChange={(event) => setFiles(Array.from(event.target.files || []))} required /></label>
        <label className="text-[13px] font-semibold">Cấp học<select className="apple-input mt-2 w-full" value={educationLevel} onChange={(event) => setEducationLevel(event.target.value)}><option value="THPT">THPT</option><option value="THCS">THCS</option><option value="TIỂU HỌC">Tiểu học</option></select></label>
        <label className="text-[13px] font-semibold">Môn học<select className="apple-input mt-2 w-full" value={subject} onChange={(event) => setSubject(event.target.value)}><option value="math">Toán</option><option value="physics">Vật lý</option><option value="chemistry">Hóa học</option><option value="biology">Sinh học</option></select></label>
        <label className="text-[13px] font-semibold">Chương trình<input className="apple-input mt-2 w-full" value={targetProgram} onChange={(event) => setTargetProgram(event.target.value)} required /></label>
        <label className="text-[13px] font-semibold">Chương<input className="apple-input mt-2 w-full" value={chapterId} onChange={(event) => setChapterId(event.target.value)} /></label>
        <label className="text-[13px] font-semibold">Bài học<input className="apple-input mt-2 w-full" value={lessonId} onChange={(event) => setLessonId(event.target.value)} /></label>
        <label className="text-[13px] font-semibold">Concept IDs<input className="apple-input mt-2 w-full" value={conceptIds} onChange={(event) => setConceptIds(event.target.value)} placeholder="dao_ham cuc_tri" /></label>
        {busy && <div className="md:col-span-2"><div className="h-2 overflow-hidden rounded-full bg-surface-quiet"><div className="h-full bg-brand transition-[width]" style={{ width: `${progress}%` }} /></div><p className="mt-1 text-[11px] text-ink-muted">Tiến độ {progress} phần trăm</p></div>}
        <button className="apple-button md:col-span-2" disabled={busy || !files.length || !title.trim()}>{busy ? "Đang xử lý" : `Tải lên và lập chỉ mục ${files.length || ""}`}</button>
      </form>
      {notice && <p className="rounded-control bg-brand-soft p-3 text-brand">{notice}</p>}
      {error && <p role="alert" className="rounded-control bg-danger-soft p-3 text-danger">{error}</p>}
      <section className="rounded-panel border border-border bg-surface"><div className="grid gap-3 border-b border-border p-4 md:grid-cols-4"><input className="apple-input md:col-span-2" value={materialSearch} onChange={(event) => setMaterialSearch(event.target.value)} placeholder="Tìm tài liệu theo từ khóa hoặc vector" /><select className="apple-input" value={subjectFilter} onChange={(event) => setSubjectFilter(event.target.value)}><option value="">Mọi môn học</option><option value="math">Toán</option><option value="physics">Vật lý</option><option value="chemistry">Hóa học</option><option value="biology">Sinh học</option></select><select className="apple-input" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="">Mọi trạng thái</option><option value="queued">Đang chờ</option><option value="indexing">Đang lập chỉ mục</option><option value="indexed">Đã lập chỉ mục</option><option value="failed">Lỗi</option></select><input className="apple-input" value={topicFilter} onChange={(event) => setTopicFilter(event.target.value)} placeholder="Topic concept skill" /><select className="apple-input" value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}><option value="">Mọi loại tệp</option>{["pdf", "docx", "pptx", "txt", "markdown", "latex", "png", "jpg", "jpeg", "webp"].map((value) => <option key={value} value={value}>{value}</option>)}</select><label className="text-[11px] font-semibold text-ink-muted">Từ ngày<input className="apple-input mt-1 w-full" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} /></label><label className="text-[11px] font-semibold text-ink-muted">Đến ngày<input className="apple-input mt-1 w-full" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} /></label><button type="button" className="apple-button-secondary md:col-span-4" disabled={busy || !materialSearch.trim()} onClick={() => void searchIndexedContent()}>Tìm trong nội dung đã lập chỉ mục</button></div>{semanticResults.length > 0 && <div className="border-b border-border p-4"><p className="text-[12px] font-semibold">Kết quả tìm trong nội dung riêng</p><div className="mt-3 grid gap-2 md:grid-cols-2">{semanticResults.map((result, index) => <div key={`${String(result.metadata?.chunk_id || result.metadata?.document_id)}-${index}`} className="rounded-control bg-surface-quiet p-3 text-[12px]"><p className="font-semibold">{result.metadata?.title || result.metadata?.document_id}</p><p className="mt-1 line-clamp-4 text-ink-muted">{result.text}</p><p className="mt-1">Score {Number(result.score || 0).toFixed(3)}</p></div>)}</div>{semanticConflicts.length > 0 && <p className="mt-3 rounded-control bg-warning-soft p-3 text-[12px] text-warning">Có {semanticConflicts.length} xung đột với nguồn khác cần giáo viên rà soát và tài liệu riêng không tự ghi đè curriculum</p>}</div>}<div className="divide-y divide-border">{visibleMaterials.map((material) => { const mapping = mappings[material._id]; const indexingStatus = material.indexing_status || (material.is_indexed ? "indexed" : "queued"); return <div key={material._id} className="space-y-3 px-5 py-4"><div className="flex flex-wrap items-center justify-between gap-2"><p className="font-semibold">{material.title}</p><div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-surface-quiet px-2 py-1 text-[11px] font-semibold">{indexingStatus === "indexed" ? "Đã lập chỉ mục" : indexingStatus === "failed" ? "Lập chỉ mục lỗi" : indexingStatus === "indexing" ? "Đang lập chỉ mục" : "Đang chờ"}</span><a className="apple-button-secondary" href={`/tai-lieu/xem-truoc/${material._id}`}>Xem trước</a><button type="button" className="apple-button-secondary" onClick={() => void renameMaterial(material)}>Đổi tên</button><button type="button" className="apple-button-secondary text-danger" onClick={() => void removeMaterial(material._id)}>Xóa</button>{indexingStatus === "failed" && <button type="button" className="apple-button-secondary" disabled={busy} onClick={() => retryIndexing(material._id)}>Thử lại</button>}</div></div><p className="text-[12px] text-ink-muted">{material.education_metadata?.subject} · {material.education_metadata?.target_program} · {mapping?.mapping_status || "Chưa có ánh xạ"} · confidence {mapping?.mapping_confidence ?? 0} · source version {material.education_metadata?.source_version || "chưa có"} · cập nhật {material.updated_at ? new Date(material.updated_at).toLocaleDateString("vi-VN") : "chưa có"}</p>{material.indexing_error && <p className="text-[12px] text-danger">Mã lỗi {material.indexing_error}</p>}{material.extracted_text && <details className="rounded-control border border-border p-3 text-[12px]"><summary className="cursor-pointer font-semibold">Văn bản đã trích xuất</summary><pre className="mt-2 max-h-60 overflow-auto whitespace-pre-wrap">{String(material.extracted_text)}</pre></details>}<label className="block text-[12px] font-semibold text-ink-muted">Thay phiên bản nguồn<input className="apple-input mt-1 w-full" type="file" accept=".pdf,.docx,.pptx,.txt,.md,.tex,.png,.jpg,.jpeg,.webp" disabled={busy} onChange={(event) => { const replacement = event.target.files?.[0]; if (replacement) void replaceMaterialVersion(material, replacement); }} /></label>{mapping && <div className="grid gap-2 md:grid-cols-3"><label className="text-[12px] font-semibold text-ink-muted">Curriculum node IDs<input className="apple-input mt-1 w-full" value={mappingNodes[material._id] || ""} onChange={(event) => setMappingNodes((current) => ({ ...current, [material._id]: event.target.value }))} /></label><label className="text-[12px] font-semibold text-ink-muted">Concept IDs<input className="apple-input mt-1 w-full" value={mappingConcepts[material._id] || ""} onChange={(event) => setMappingConcepts((current) => ({ ...current, [material._id]: event.target.value }))} /></label><label className="text-[12px] font-semibold text-ink-muted">Skill IDs<input className="apple-input mt-1 w-full" value={mappingSkills[material._id] || ""} onChange={(event) => setMappingSkills((current) => ({ ...current, [material._id]: event.target.value }))} /></label><div className="flex gap-2 md:col-span-3"><button type="button" className="apple-button-secondary" disabled={busy} onClick={() => reviewMapping(material._id, "needs_review")}>Cần rà soát</button><button type="button" className="apple-button" disabled={busy} onClick={() => reviewMapping(material._id, "confirmed")}>Lưu và xác nhận ánh xạ</button></div></div>}</div>; })}{!visibleMaterials.length && <p className="px-5 py-10 text-center text-[13px] text-ink-muted">Không có tài liệu phù hợp bộ lọc</p>}</div></section>
      {visibleMaterials.some((material) => material.extracted_text_available || material.index_report?.failed_chunks?.length || material.index_report?.quarantined_chunks?.length) && <section className="rounded-panel border border-border bg-surface"><div className="border-b border-border px-5 py-4"><h2 className="font-semibold">Kết quả trích xuất và lập chỉ mục</h2></div><div className="divide-y divide-border">{visibleMaterials.filter((material) => material.extracted_text_available || material.index_report?.failed_chunks?.length || material.index_report?.quarantined_chunks?.length).map((material) => { const text = extractedText[material._id]; return <div key={material._id} className="space-y-3 px-5 py-4"><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-[13px] font-semibold">{material.title}</p>{material.extracted_text_available && <button type="button" className="apple-button-secondary" disabled={busy} onClick={() => void loadExtractedText(material._id)}>{text !== undefined ? "Ẩn văn bản" : "Xem văn bản đã trích xuất"}</button>}</div>{material.index_report?.failed_chunks?.length > 0 && <p className="text-[12px] text-danger">Có {material.index_report.failed_chunks.length} chunk lập chỉ mục lỗi</p>}{material.index_report?.quarantined_chunks?.length > 0 && <p className="text-[12px] text-warning">Có {material.index_report.quarantined_chunks.length} chunk bị cách ly an toàn</p>}{text !== undefined && <div className="rounded-control border border-border p-3 text-[12px]"><pre className="max-h-72 overflow-auto whitespace-pre-wrap">{text || "Không có văn bản"}</pre>{material.extracted_text_truncated && <p className="mt-2 text-warning">Bản xem trước đã được giới hạn kích thước</p>}</div>}</div>; })}</div></section>}
    </div>
  );
}
