"use client";

function valueText(value) {
  if (value === undefined) return "Không có";
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

export default function ProposalDiffPanel({ proposal }) {
  const patch = proposal.patch || {};
  const base = proposal.base_version || {};
  const fields = Object.keys(patch);
  if (!fields.length) return <p className="text-[12px] text-ink-muted">Không có trường thay đổi</p>;
  return (
    <div className="max-w-3xl overflow-x-auto">
      <table className="w-full text-left text-[11px]" aria-label="So sánh phiên bản gốc và đề xuất">
        <thead>
          <tr className="border-b border-border text-ink-muted">
            <th className="p-2 font-semibold">Trường</th>
            <th className="p-2 font-semibold">Phiên bản gốc</th>
            <th className="p-2 font-semibold">Đề xuất</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {fields.map((field) => (
            <tr key={field}>
              <th className="p-2 align-top font-semibold">{field}</th>
              <td className="p-2 align-top">
                <pre className="max-w-sm whitespace-pre-wrap break-words">
                  {valueText(base[field])}
                </pre>
              </td>
              <td className="bg-brand-soft/30 p-2 align-top">
                <pre className="max-w-sm whitespace-pre-wrap break-words">
                  {valueText(patch[field])}
                </pre>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
