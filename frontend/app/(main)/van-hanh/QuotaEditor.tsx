"use client";

import { useEffect, useState } from "react";
import { Button } from "@/shared/components/ui/Button";

const labels: Record<string, string> = {
  BASIC: "Cơ bản",
  PRO: "Chuyên sâu",
  PREMIUM: "Toàn năng",
  admin: "Quản trị viên",
};

export default function QuotaEditor({
  quotas,
  processing,
  onSave,
}: {
  quotas: Record<string, any>;
  processing: string;
  onSave: (role: string, values: any) => Promise<boolean>;
}) {
  const [drafts, setDrafts] = useState<Record<string, any>>(quotas);
  useEffect(() => setDrafts(quotas), [quotas]);
  const roles = ["BASIC", "PRO", "PREMIUM", "admin"].filter(
    (role) => drafts[role],
  );

  return (
    <div className="overflow-x-auto rounded-panel border border-border bg-surface">
      <table className="w-full min-w-[980px] border-collapse text-left">
        <thead className="bg-surface-quiet text-[12px] font-semibold text-ink-muted">
          <tr>
            <th className="px-4 py-3">Gói</th>
            <th className="px-4 py-3">Yêu cầu mỗi tuần</th>
            <th className="px-4 py-3">Token mỗi tuần</th>
            <th className="px-4 py-3">Yêu cầu mỗi ngày</th>
            <th className="px-4 py-3">Token mỗi ngày</th>
            <th className="px-4 py-3">Tài liệu tối đa</th>
            <th className="px-4 py-3 text-right">Thao tác</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {roles.map((role) => {
            const admin = role === "admin";
            const update = (field: string, value: string) =>
              setDrafts((current) => ({
                ...current,
                [role]: {
                  ...current[role],
                  [field]: Math.max(0, Number(value) || 0),
                },
              }));
            return (
              <tr key={role} className="text-[13px]">
                <td className="px-4 py-3.5 font-semibold text-ink">
                  {labels[role]}
                </td>
                <td className="px-4 py-3.5">
                  <input
                    aria-label={`Yêu cầu tuần của ${labels[role]}`}
                    type="number"
                    min={0}
                    readOnly={admin}
                    value={admin ? 0 : drafts[role].weekly_requests || 0}
                    onChange={(event) =>
                      update("weekly_requests", event.target.value)
                    }
                    className="apple-input min-h-9 w-32 py-1.5 text-[13px]"
                  />
                </td>
                <td className="px-4 py-3.5">
                  <input
                    aria-label={`Token tuần của ${labels[role]}`}
                    type="number"
                    min={0}
                    readOnly={admin}
                    value={admin ? 0 : drafts[role].weekly_tokens || 0}
                    onChange={(event) =>
                      update("weekly_tokens", event.target.value)
                    }
                    className="apple-input min-h-9 w-36 py-1.5 text-[13px]"
                  />
                </td>
                <td className="px-4 py-3.5">
                  <input
                    aria-label={`Yêu cầu của ${labels[role]}`}
                    type="number"
                    min={0}
                    readOnly={admin}
                    value={admin ? 0 : drafts[role].daily_requests || 0}
                    onChange={(event) =>
                      update("daily_requests", event.target.value)
                    }
                    className="apple-input min-h-9 w-32 py-1.5 text-[13px]"
                  />
                </td>
                <td className="px-4 py-3.5">
                  <input
                    aria-label={`Token của ${labels[role]}`}
                    type="number"
                    min={0}
                    readOnly={admin}
                    value={admin ? 0 : drafts[role].daily_tokens || 0}
                    onChange={(event) =>
                      update("daily_tokens", event.target.value)
                    }
                    className="apple-input min-h-9 w-36 py-1.5 text-[13px]"
                  />
                </td>
                <td className="px-4 py-3.5">
                  <input
                    aria-label={`Tài liệu của ${labels[role]}`}
                    type="number"
                    min={0}
                    readOnly={admin}
                    value={admin ? 0 : drafts[role].max_docs || 0}
                    onChange={(event) => update("max_docs", event.target.value)}
                    className="apple-input min-h-9 w-28 py-1.5 text-[13px]"
                  />
                </td>
                <td className="px-4 py-3.5 text-right">
                  {!admin && (
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={Boolean(processing)}
                      onClick={() => onSave(role, drafts[role])}
                    >
                      {processing === `quota-${role}` ? "Đang lưu" : "Lưu"}
                    </Button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
