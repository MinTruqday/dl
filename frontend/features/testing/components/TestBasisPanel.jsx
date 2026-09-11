import DataTable from "./DataTable";


export default function TestBasisPanel({ refs, onChange, requirements }) {
  const addRequirement = (event) => {
    const artifactVersionId = event.target.value;
    if (!artifactVersionId || refs.some((item) => item.artifact_version_id === artifactVersionId)) return;
    const requirement = requirements.find((item) => item.current_version_id === artifactVersionId);
    onChange([...refs, { artifact_type: "REQUIREMENT_VERSION", artifact_id: requirement?._id || artifactVersionId, artifact_version_id: artifactVersionId }]);
    event.target.value = "";
  };
  return (
    <fieldset className="space-y-3 rounded-2xl border border-border p-4">
      <legend className="px-2 text-sm font-semibold">Test Basis</legend>
      <select className="apple-input" aria-label="Thêm phiên bản yêu cầu làm test basis" defaultValue="" onChange={addRequirement}>
        <option value="">Chọn yêu cầu đã baseline</option>
        {requirements.map((item) => <option key={item.current_version_id} value={item.current_version_id}>{item.requirement_key} {item.current_version?.title || item.title}</option>)}
      </select>
      <DataTable
        items={refs}
        empty="Phải chọn ít nhất một test basis"
        columns={[
          { key: "artifact_type", label: "Loại" },
          { key: "artifact_version_id", label: "Phiên bản", render: (item) => item.artifact_version_id || item.artifact_id },
          { key: "actions", label: "Thao tác", render: (item) => <button className="secondary-button" type="button" onClick={() => onChange(refs.filter((value) => value !== item))}>Bỏ</button> },
        ]}
      />
    </fieldset>
  );
}
