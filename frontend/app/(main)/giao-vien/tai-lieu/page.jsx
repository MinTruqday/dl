"use client";
import { useEffect, useState } from "react";
import { uploadDocumentAPI } from "@/features/cloud/services/upload.service";
import { createDocumentAPI, deleteAuthorDocumentAPI, getDocumentDraftAPI, getMyDocumentsAPI, retryDocumentIndexingAPI, updateDocumentAPI } from "@/features/content/services/document.service";
import { createTeacherMaterialMapping, listSourceMappings, reviewSourceMapping, searchTeacherMaterials } from "@/features/assessment/services/assessment.service";
function slugOf(value) {
    return value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "") || "tai-lieu-giao-vien";
}
function extensionOf(file) {
    var _a;
    const extension = ((_a = file.name.split(".").pop()) === null || _a === void 0 ? void 0 : _a.toLowerCase()) || "txt";
    return extension === "md" ? "markdown" : extension === "tex" ? "latex" : extension;
}
async function sha256(file) {
    const bytes = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
    return Array.from(new Uint8Array(bytes), (value) => value.toString(16).padStart(2, "0")).join("");
}
export default function TeacherMaterialPage() {
    const [materials, setMaterials] = useState([]);
    const [mappings, setMappings] = useState({});
    const [mappingConcepts, setMappingConcepts] = useState({});
    const [mappingNodes, setMappingNodes] = useState({});
    const [mappingSkills, setMappingSkills] = useState({});
    const [title, setTitle] = useState("");
    const [files, setFiles] = useState([]);
    const [progress, setProgress] = useState(0);
    const [materialSearch, setMaterialSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState("");
    const [subjectFilter, setSubjectFilter] = useState("");
    const [topicFilter, setTopicFilter] = useState("");
    const [typeFilter, setTypeFilter] = useState("");
    const [dateFrom, setDateFrom] = useState("");
    const [dateTo, setDateTo] = useState("");
    const [semanticResults, setSemanticResults] = useState([]);
    const [semanticConflicts, setSemanticConflicts] = useState([]);
    const [extractedText, setExtractedText] = useState({});
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
        var _a, _b;
        const response = await getMyDocumentsAPI("", "", 100);
        const rows = (_b = (_a = response.data) !== null && _a !== void 0 ? _a : response) !== null && _b !== void 0 ? _b : [];
        const teacherMaterials = rows.filter((row) => { var _a; return ((_a = row.education_metadata) === null || _a === void 0 ? void 0 : _a.source_type) === "teacher_material"; });
        const mappingRows = await Promise.all(teacherMaterials.map(async (row) => [row._id, (await listSourceMappings(row._id))[0]]));
        setMaterials(teacherMaterials);
        setMappings(Object.fromEntries(mappingRows.filter(([, mapping]) => mapping)));
        setMappingConcepts(Object.fromEntries(mappingRows.map(([documentId, mapping]) => [documentId, ((mapping === null || mapping === void 0 ? void 0 : mapping.concept_ids) || []).join(", ")])));
        setMappingNodes(Object.fromEntries(mappingRows.map(([documentId, mapping]) => [documentId, ((mapping === null || mapping === void 0 ? void 0 : mapping.curriculum_node_ids) || []).join(", ")])));
        setMappingSkills(Object.fromEntries(mappingRows.map(([documentId, mapping]) => [documentId, ((mapping === null || mapping === void 0 ? void 0 : mapping.skill_ids) || []).join(", ")])));
    };
    useEffect(() => {
        load().catch((reason) => setError(reason instanceof Error ? reason.message : "Không thể tải tài liệu giáo viên"));
    }, []);
    const submit = async (event) => {
        var _a, _b, _c, _d, _e, _f, _g, _h, _j, _k;
        event.preventDefault();
        if (!files.length || !title.trim())
            return;
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
                    documentId = (_e = (_d = (_b = (_a = created.data) === null || _a === void 0 ? void 0 : _a._id) !== null && _b !== void 0 ? _b : (_c = created.data) === null || _c === void 0 ? void 0 : _c.id) !== null && _d !== void 0 ? _d : created._id) !== null && _e !== void 0 ? _e : created.id;
                    const [uploaded, sourceVersion] = await Promise.all([uploadDocumentAPI(file), sha256(file)]);
                    const fileUrl = (_g = (_f = uploaded.data) === null || _f === void 0 ? void 0 : _f.url) !== null && _g !== void 0 ? _g : (_h = uploaded.data) === null || _h === void 0 ? void 0 : _h.file_path;
                    if (!fileUrl)
                        throw new Error("Không nhận được đường dẫn tệp đã tải lên");
                    const concepts = conceptIds.split(/[,;\n]+/).map((value) => value.trim()).filter(Boolean);
                    await updateDocumentAPI(documentId, {
                        file_url: fileUrl,
                        content_format: (_k = (_j = uploaded.data) === null || _j === void 0 ? void 0 : _j.extension) !== null && _k !== void 0 ? _k : extensionOf(file),
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
                }
                catch (reason) {
                    if (documentId)
                        await deleteAuthorDocumentAPI(documentId).catch(() => undefined);
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
        }
        catch (reason) {
            setError(reason instanceof Error ? reason.message : "Không thể tải tài liệu giáo viên");
        }
        finally {
            setBusy(false);
        }
    };
    const renameMaterial = async (material) => {
        const nextTitle = window.prompt("Tên tài liệu mới", material.title || "");
        if (!(nextTitle === null || nextTitle === void 0 ? void 0 : nextTitle.trim()))
            return;
        await updateDocumentAPI(material._id, { title: nextTitle.trim() });
        setNotice("Đã đổi tên tài liệu");
        await load();
    };
    const removeMaterial = async (materialId) => {
        if (!window.confirm("Xóa tài liệu riêng này"))
            return;
        await deleteAuthorDocumentAPI(materialId);
        setNotice("Đã chuyển tài liệu khỏi thư viện riêng");
        await load();
    };
    const replaceMaterialVersion = async (material, replacement) => {
        var _a, _b, _c, _d, _e;
        setBusy(true);
        setError("");
        try {
            const [uploaded, sourceVersion] = await Promise.all([uploadDocumentAPI(replacement), sha256(replacement)]);
            const fileUrl = (_b = (_a = uploaded.data) === null || _a === void 0 ? void 0 : _a.url) !== null && _b !== void 0 ? _b : (_c = uploaded.data) === null || _c === void 0 ? void 0 : _c.file_path;
            if (!fileUrl)
                throw new Error("Không nhận được đường dẫn tệp đã tải lên");
            await updateDocumentAPI(material._id, {
                file_url: fileUrl,
                content_format: (_e = (_d = uploaded.data) === null || _d === void 0 ? void 0 : _d.extension) !== null && _e !== void 0 ? _e : extensionOf(replacement),
                education_metadata: Object.assign(Object.assign({}, material.education_metadata), { source_version: sourceVersion, mapping_status: "needs_review" }),
            });
            const currentMapping = mappings[material._id];
            await createTeacherMaterialMapping(material._id, {
                chunk_id: `document-${material._id}-${sourceVersion.slice(0, 16)}`,
                curriculum_node_ids: (currentMapping === null || currentMapping === void 0 ? void 0 : currentMapping.curriculum_node_ids) || [],
                concept_ids: (currentMapping === null || currentMapping === void 0 ? void 0 : currentMapping.concept_ids) || [],
                skill_ids: (currentMapping === null || currentMapping === void 0 ? void 0 : currentMapping.skill_ids) || [],
                mapping_confidence: (currentMapping === null || currentMapping === void 0 ? void 0 : currentMapping.mapping_confidence) || 0.4,
                mapping_status: "needs_review",
                source_version: sourceVersion,
            });
            await retryDocumentIndexingAPI(material._id);
            setNotice("Đã tạo phiên bản nguồn mới và đưa vào hàng đợi lập chỉ mục lại");
            await load();
        }
        catch (reason) {
            setError(reason instanceof Error ? reason.message : "Không thể thay phiên bản tài liệu");
        }
        finally {
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
        if (!materialSearch.trim())
            return;
        setBusy(true);
        setError("");
        try {
            const result = await searchTeacherMaterials(materialSearch.trim(), subjectFilter);
            setSemanticResults(result.documents || []);
            setSemanticConflicts(result.conflicts || []);
        }
        catch (reason) {
            setError(reason instanceof Error ? reason.message : "Không thể tìm trong nội dung đã lập chỉ mục");
        }
        finally {
            setBusy(false);
        }
    };
    const reviewMapping = async (documentId, mappingStatus) => {
        const mapping = mappings[documentId];
        if (!mapping)
            return;
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
        }
        catch (reason) {
            setError(reason instanceof Error ? reason.message : "Không thể cập nhật ánh xạ tài liệu");
        }
        finally {
            setBusy(false);
        }
    };
    const retryIndexing = async (documentId) => {
        setBusy(true);
        setError("");
        setNotice("");
        try {
            await retryDocumentIndexingAPI(documentId);
            setNotice("Đã đưa tài liệu vào hàng đợi lập chỉ mục");
            await load();
        }
        catch (reason) {
            setError(reason instanceof Error ? reason.message : "Không thể lập chỉ mục lại tài liệu");
        }
        finally {
            setBusy(false);
        }
    };
    const loadExtractedText = async (documentId) => {
        var _a;
        if (extractedText[documentId] !== undefined) {
            setExtractedText((current) => {
                const next = Object.assign({}, current);
                delete next[documentId];
                return next;
            });
            return;
        }
        setBusy(true);
        setError("");
        try {
            const response = await getDocumentDraftAPI(documentId);
            const document = (_a = response.data) !== null && _a !== void 0 ? _a : response;
            setExtractedText((current) => (Object.assign(Object.assign({}, current), { [documentId]: String(document.extracted_text || "") })));
        }
        catch (reason) {
            setError(reason instanceof Error ? reason.message : "Không thể tải văn bản đã trích xuất");
        }
        finally {
            setBusy(false);
        }
    };
    return (<div className="mx-auto max-w-[1200px] space-y-6 p-5 md:p-8">
      <div><p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">Teacher Material</p><h1 className="mt-2 text-[30px] font-semibold">Tài liệu bổ trợ riêng</h1><p className="mt-2 text-[13px] text-ink-muted">Tài liệu chỉ được truy xuất trong phạm vi chủ sở hữu và không thay thế curriculum chính thống</p></div>
      <form className="grid gap-4 rounded-panel border border-border bg-surface p-5 md:grid-cols-2" onSubmit={submit}>
        <label className="text-[13px] font-semibold">Tên tài liệu<input className="apple-input mt-2 w-full" value={title} onChange={(event) => setTitle(event.target.value)} required/></label>
        <label className="text-[13px] font-semibold">Tệp nguồn<input className="apple-input mt-2 w-full" type="file" multiple accept=".pdf,.docx,.pptx,.txt,.md,.tex,.png,.jpg,.jpeg,.webp" onChange={(event) => setFiles(Array.from(event.target.files || []))} required/></label>
        <label className="text-[13px] font-semibold">Cấp học<select className="apple-input mt-2 w-full" value={educationLevel} onChange={(event) => setEducationLevel(event.target.value)}><option value="THPT">THPT</option><option value="THCS">THCS</option><option value="TIỂU HỌC">Tiểu học</option></select></label>
        <label className="text-[13px] font-semibold">Môn học<select className="apple-input mt-2 w-full" value={subject} onChange={(event) => setSubject(event.target.value)}><option value="math">Toán</option><option value="physics">Vật lý</option><option value="chemistry">Hóa học</option><option value="biology">Sinh học</option></select></label>
        <label className="text-[13px] font-semibold">Chương trình<input className="apple-input mt-2 w-full" value={targetProgram} onChange={(event) => setTargetProgram(event.target.value)} required/></label>
        <label className="text-[13px] font-semibold">Chương<input className="apple-input mt-2 w-full" value={chapterId} onChange={(event) => setChapterId(event.target.value)}/></label>
        <label className="text-[13px] font-semibold">Bài học<input className="apple-input mt-2 w-full" value={lessonId} onChange={(event) => setLessonId(event.target.value)}/></label>
        <label className="text-[13px] font-semibold">Concept IDs<input className="apple-input mt-2 w-full" value={conceptIds} onChange={(event) => setConceptIds(event.target.value)} placeholder="dao_ham cuc_tri"/></label>
        {busy && <div className="md:col-span-2"><div className="h-2 overflow-hidden rounded-full bg-surface-quiet"><div className="h-full bg-brand transition-[width]" style={{ width: `${progress}%` }}/></div><p className="mt-1 text-[11px] text-ink-muted">Tiến độ {progress} phần trăm</p></div>}
        <button className="apple-button md:col-span-2" disabled={busy || !files.length || !title.trim()}>{busy ? "Đang xử lý" : `Tải lên và lập chỉ mục ${files.length || ""}`}</button>
      </form>
      {notice && <p className="rounded-control bg-brand-soft p-3 text-brand">{notice}</p>}
      {error && <p role="alert" className="rounded-control bg-danger-soft p-3 text-danger">{error}</p>}
      <section className="rounded-panel border border-border bg-surface"><div className="grid gap-3 border-b border-border p-4 md:grid-cols-4"><input className="apple-input md:col-span-2" value={materialSearch} onChange={(event) => setMaterialSearch(event.target.value)} placeholder="Tìm tài liệu theo từ khóa hoặc vector"/><select className="apple-input" value={subjectFilter} onChange={(event) => setSubjectFilter(event.target.value)}><option value="">Mọi môn học</option><option value="math">Toán</option><option value="physics">Vật lý</option><option value="chemistry">Hóa học</option><option value="biology">Sinh học</option></select><select className="apple-input" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="">Mọi trạng thái</option><option value="queued">Đang chờ</option><option value="indexing">Đang lập chỉ mục</option><option value="indexed">Đã lập chỉ mục</option><option value="failed">Lỗi</option></select><input className="apple-input" value={topicFilter} onChange={(event) => setTopicFilter(event.target.value)} placeholder="Topic concept skill"/><select className="apple-input" value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}><option value="">Mọi loại tệp</option>{["pdf", "docx", "pptx", "txt", "markdown", "latex", "png", "jpg", "jpeg", "webp"].map((value) => <option key={value} value={value}>{value}</option>)}</select><label className="text-[11px] font-semibold text-ink-muted">Từ ngày<input className="apple-input mt-1 w-full" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)}/></label><label className="text-[11px] font-semibold text-ink-muted">Đến ngày<input className="apple-input mt-1 w-full" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)}/></label><button type="button" className="apple-button-secondary md:col-span-4" disabled={busy || !materialSearch.trim()} onClick={() => void searchIndexedContent()}>Tìm trong nội dung đã lập chỉ mục</button></div>{semanticResults.length > 0 && <div className="border-b border-border p-4"><p className="text-[12px] font-semibold">Kết quả tìm trong nội dung riêng</p><div className="mt-3 grid gap-2 md:grid-cols-2">{semanticResults.map((result, index) => { var _a, _b, _c, _d; return <div key={`${String(((_a = result.metadata) === null || _a === void 0 ? void 0 : _a.chunk_id) || ((_b = result.metadata) === null || _b === void 0 ? void 0 : _b.document_id))}-${index}`} className="rounded-control bg-surface-quiet p-3 text-[12px]"><p className="font-semibold">{((_c = result.metadata) === null || _c === void 0 ? void 0 : _c.title) || ((_d = result.metadata) === null || _d === void 0 ? void 0 : _d.document_id)}</p><p className="mt-1 line-clamp-4 text-ink-muted">{result.text}</p><p className="mt-1">Score {Number(result.score || 0).toFixed(3)}</p></div>; })}</div>{semanticConflicts.length > 0 && <p className="mt-3 rounded-control bg-warning-soft p-3 text-[12px] text-warning">Có {semanticConflicts.length} xung đột với nguồn khác cần giáo viên rà soát và tài liệu riêng không tự ghi đè curriculum</p>}</div>}<div className="divide-y divide-border">{visibleMaterials.map((material) => { var _a, _b, _c, _d; const mapping = mappings[material._id]; const indexingStatus = material.indexing_status || (material.is_indexed ? "indexed" : "queued"); return <div key={material._id} className="space-y-3 px-5 py-4"><div className="flex flex-wrap items-center justify-between gap-2"><p className="font-semibold">{material.title}</p><div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-surface-quiet px-2 py-1 text-[11px] font-semibold">{indexingStatus === "indexed" ? "Đã lập chỉ mục" : indexingStatus === "failed" ? "Lập chỉ mục lỗi" : indexingStatus === "indexing" ? "Đang lập chỉ mục" : "Đang chờ"}</span><a className="apple-button-secondary" href={`/tai-lieu/xem-truoc/${material._id}`}>Xem trước</a><button type="button" className="apple-button-secondary" onClick={() => void renameMaterial(material)}>Đổi tên</button><button type="button" className="apple-button-secondary text-danger" onClick={() => void removeMaterial(material._id)}>Xóa</button>{indexingStatus === "failed" && <button type="button" className="apple-button-secondary" disabled={busy} onClick={() => retryIndexing(material._id)}>Thử lại</button>}</div></div><p className="text-[12px] text-ink-muted">{(_a = material.education_metadata) === null || _a === void 0 ? void 0 : _a.subject} · {(_b = material.education_metadata) === null || _b === void 0 ? void 0 : _b.target_program} · {(mapping === null || mapping === void 0 ? void 0 : mapping.mapping_status) || "Chưa có ánh xạ"} · confidence {(_c = mapping === null || mapping === void 0 ? void 0 : mapping.mapping_confidence) !== null && _c !== void 0 ? _c : 0} · source version {((_d = material.education_metadata) === null || _d === void 0 ? void 0 : _d.source_version) || "chưa có"} · cập nhật {material.updated_at ? new Date(material.updated_at).toLocaleDateString("vi-VN") : "chưa có"}</p>{material.indexing_error && <p className="text-[12px] text-danger">Mã lỗi {material.indexing_error}</p>}{material.extracted_text && <details className="rounded-control border border-border p-3 text-[12px]"><summary className="cursor-pointer font-semibold">Văn bản đã trích xuất</summary><pre className="mt-2 max-h-60 overflow-auto whitespace-pre-wrap">{String(material.extracted_text)}</pre></details>}<label className="block text-[12px] font-semibold text-ink-muted">Thay phiên bản nguồn<input className="apple-input mt-1 w-full" type="file" accept=".pdf,.docx,.pptx,.txt,.md,.tex,.png,.jpg,.jpeg,.webp" disabled={busy} onChange={(event) => { var _a; const replacement = (_a = event.target.files) === null || _a === void 0 ? void 0 : _a[0]; if (replacement)
        void replaceMaterialVersion(material, replacement); }}/></label>{mapping && <div className="grid gap-2 md:grid-cols-3"><label className="text-[12px] font-semibold text-ink-muted">Curriculum node IDs<input className="apple-input mt-1 w-full" value={mappingNodes[material._id] || ""} onChange={(event) => setMappingNodes((current) => (Object.assign(Object.assign({}, current), { [material._id]: event.target.value })))}/></label><label className="text-[12px] font-semibold text-ink-muted">Concept IDs<input className="apple-input mt-1 w-full" value={mappingConcepts[material._id] || ""} onChange={(event) => setMappingConcepts((current) => (Object.assign(Object.assign({}, current), { [material._id]: event.target.value })))}/></label><label className="text-[12px] font-semibold text-ink-muted">Skill IDs<input className="apple-input mt-1 w-full" value={mappingSkills[material._id] || ""} onChange={(event) => setMappingSkills((current) => (Object.assign(Object.assign({}, current), { [material._id]: event.target.value })))}/></label><div className="flex gap-2 md:col-span-3"><button type="button" className="apple-button-secondary" disabled={busy} onClick={() => reviewMapping(material._id, "needs_review")}>Cần rà soát</button><button type="button" className="apple-button" disabled={busy} onClick={() => reviewMapping(material._id, "confirmed")}>Lưu và xác nhận ánh xạ</button></div></div>}</div>; })}{!visibleMaterials.length && <p className="px-5 py-10 text-center text-[13px] text-ink-muted">Không có tài liệu phù hợp bộ lọc</p>}</div></section>
      {visibleMaterials.some((material) => { var _a, _b, _c, _d; return material.extracted_text_available || ((_b = (_a = material.index_report) === null || _a === void 0 ? void 0 : _a.failed_chunks) === null || _b === void 0 ? void 0 : _b.length) || ((_d = (_c = material.index_report) === null || _c === void 0 ? void 0 : _c.quarantined_chunks) === null || _d === void 0 ? void 0 : _d.length); }) && <section className="rounded-panel border border-border bg-surface"><div className="border-b border-border px-5 py-4"><h2 className="font-semibold">Kết quả trích xuất và lập chỉ mục</h2></div><div className="divide-y divide-border">{visibleMaterials.filter((material) => { var _a, _b, _c, _d; return material.extracted_text_available || ((_b = (_a = material.index_report) === null || _a === void 0 ? void 0 : _a.failed_chunks) === null || _b === void 0 ? void 0 : _b.length) || ((_d = (_c = material.index_report) === null || _c === void 0 ? void 0 : _c.quarantined_chunks) === null || _d === void 0 ? void 0 : _d.length); }).map((material) => { var _a, _b, _c, _d; const text = extractedText[material._id]; return <div key={material._id} className="space-y-3 px-5 py-4"><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-[13px] font-semibold">{material.title}</p>{material.extracted_text_available && <button type="button" className="apple-button-secondary" disabled={busy} onClick={() => void loadExtractedText(material._id)}>{text !== undefined ? "Ẩn văn bản" : "Xem văn bản đã trích xuất"}</button>}</div>{((_b = (_a = material.index_report) === null || _a === void 0 ? void 0 : _a.failed_chunks) === null || _b === void 0 ? void 0 : _b.length) > 0 && <p className="text-[12px] text-danger">Có {material.index_report.failed_chunks.length} chunk lập chỉ mục lỗi</p>}{((_d = (_c = material.index_report) === null || _c === void 0 ? void 0 : _c.quarantined_chunks) === null || _d === void 0 ? void 0 : _d.length) > 0 && <p className="text-[12px] text-warning">Có {material.index_report.quarantined_chunks.length} chunk bị cách ly an toàn</p>}{text !== undefined && <div className="rounded-control border border-border p-3 text-[12px]"><pre className="max-h-72 overflow-auto whitespace-pre-wrap">{text || "Không có văn bản"}</pre>{material.extracted_text_truncated && <p className="mt-2 text-warning">Bản xem trước đã được giới hạn kích thước</p>}</div>}</div>; })}</div></section>}
    </div>);
}
