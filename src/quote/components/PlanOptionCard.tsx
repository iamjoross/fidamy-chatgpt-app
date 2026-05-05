import { CheckCircle2 } from "lucide-react";
import type { BillingPeriod, Plan, PlanSelection } from "../types";
import { formatAmount, formatPlanName, planId } from "../utils";

type PlanOptionCardProps = {
  billingPeriod: BillingPeriod;
  plan: Plan;
  isSelected: boolean;
  onSelect: (selection: PlanSelection) => void;
};

export function PlanOptionCard({
  billingPeriod,
  plan,
  isSelected,
  onSelect,
}: PlanOptionCardProps) {
  const planLabel = plan.labels?.en ?? formatPlanName(plan.plan);
  const features = Array.isArray(plan.features) ? plan.features : [];
  const selectionId = planId(billingPeriod, plan);
  const isExtended = plan.plan === "extended";

  return (
    <button
      aria-pressed={isSelected}
      className={`quote-plan-card${isSelected ? " is-selected" : ""}`}
      onClick={() =>
        onSelect({
          billingPeriod,
          id: selectionId,
          label: planLabel,
          totalPremium: plan.totalPremium ?? "",
        })
      }
      type="button"
    >
      {isSelected ? (
        <div className="quote-plan-selected-mark">
          <CheckCircle2 size={16} strokeWidth={2} />
        </div>
      ) : null}
      <div className="quote-plan-header">
        <div>
          <div className="quote-plan-title-row">
            <h3>{planLabel}</h3>
            {isExtended ? (
              <span className="quote-plan-inline-pill">Includes theft</span>
            ) : null}
          </div>
          <div className="quote-plan-price">
            <span className="quote-plan-price-amount">
              {formatAmount(plan.totalPremium)}
            </span>
            <span className="quote-plan-price-period">
              {billingPeriod === "monthly" ? "/Month" : "/Year"}
            </span>
          </div>
        </div>
      </div>
      {isExtended ? (
        <p className="quote-plan-description">
          Including all benefits of Basic Coverage, plus extra protection
          against:
        </p>
      ) : null}
      <ul className="quote-feature-list">
        {features.map((feature) => (
          <li key={feature.code ?? feature.labels?.en}>
            <CheckCircle2
              className="quote-feature-icon"
              size={14}
              strokeWidth={2}
            />
            {feature.labels?.en ?? formatPlanName(feature.code)}
          </li>
        ))}
      </ul>
    </button>
  );
}
