import { Shield } from "lucide-react";
import type { BillingPeriod, Plan, PlanSelection } from "../types";
import { PlanOptionCard } from "./PlanOptionCard";
import { planId } from "../utils";

type BillingPeriodSectionProps = {
  billingPeriod: BillingPeriod;
  plans: Plan[];
  selectedId: string;
  onSelect: (selection: PlanSelection) => void;
};

export function BillingPeriodSection({
  billingPeriod,
  plans,
  selectedId,
  onSelect,
}: BillingPeriodSectionProps) {
  if (!plans.length) {
    return null;
  }

  return (
    <section className="quote-group">
      <div className="quote-group-header">
        <div className="quote-group-icon">
          <Shield size={16} strokeWidth={1.8} />
        </div>
        <div>
          <h2>
            {billingPeriod === "monthly"
              ? "Monthly coverage"
              : "Yearly coverage"}
          </h2>
        </div>
      </div>
      <div className="quote-plan-grid">
        {plans.map((plan) => (
          <PlanOptionCard
            key={plan.plan ?? "unknown"}
            billingPeriod={billingPeriod}
            isSelected={selectedId === planId(billingPeriod, plan)}
            onSelect={onSelect}
            plan={plan}
          />
        ))}
      </div>
    </section>
  );
}
