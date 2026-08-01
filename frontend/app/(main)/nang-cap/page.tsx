"use client";

import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import InlineState from "@/app/_components/InlineState";
import PageHeader from "@/app/_components/PageHeader";
import { useMembershipPlans } from "./useMembershipPlans";

const number = new Intl.NumberFormat("vi-VN");

export default function UpgradePage() {
  const {
    plans,
    balance,
    currentTier,
    loading,
    buying,
    error,
    notice,
    reload,
    buy,
    openWallet,
  } = useMembershipPlans();

  if (loading) return <PageLoader rows={3} />;

  return (
    <div className="w-full">
      <PageHeader
        title="Gói thành viên"
        meta={`Số dư ${number.format(balance)} dl`}
        actions={
          <Button variant="secondary" onClick={openWallet}>
            Mở ví
          </Button>
        }
      />

      {error && (
        <div className="mb-6">
          <InlineState
            title="Không thể hoàn tất yêu cầu"
            detail={error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}
      {notice && (
        <div className="mb-6">
          <InlineState title={notice} />
        </div>
      )}

      <div className="overflow-hidden rounded-panel border border-border bg-surface">
        {plans.map((plan) => {
          const current = currentTier === plan.id;
          const disabled = current || plan.id === "BASIC" || Boolean(buying);
          return (
            <section
              key={plan.id}
              className="grid gap-5 border-b border-border px-5 py-6 last:border-b-0 md:grid-cols-[12rem_minmax(0,1fr)_12rem] md:items-start md:px-6"
            >
              <div>
                <h2 className="text-[19px] font-semibold text-ink">
                  {plan.name}
                </h2>
                <p className="mt-2 text-[14px] text-ink-muted">
                  {plan.price
                    ? `${number.format(plan.price)} dl mỗi 30 ngày`
                    : "Không tính phí"}
                </p>
              </div>
              <ul className="grid gap-x-6 gap-y-2 text-[14px] text-ink-muted sm:grid-cols-2">
                {plan.features.map((feature) => (
                  <li key={feature}>{feature}</li>
                ))}
              </ul>
              <div className="flex md:justify-end">
                <Button
                  variant={current ? "secondary" : "primary"}
                  disabled={disabled}
                  onClick={() => buy(plan)}
                >
                  {buying === plan.id
                    ? "Đang xử lý"
                    : current
                      ? "Đang sử dụng"
                      : plan.id === "BASIC"
                        ? "Gói mặc định"
                        : "Chọn gói"}
                </Button>
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
