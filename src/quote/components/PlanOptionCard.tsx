import { useId, useState } from "react";
import { CheckCircle2, ChevronDown, ShieldCheck } from "lucide-react";
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
  const [isExpanded, setIsExpanded] = useState(false);
  const detailsId = useId();

  return (
    <button
      aria-expanded={isExpanded}
      aria-pressed={isSelected}
      aria-controls={features.length ? detailsId : undefined}
      className={`quote-plan-card${isSelected ? " is-selected" : ""}`}
      onClick={() => {
        onSelect({
          billingPeriod,
          id: selectionId,
          label: planLabel,
          totalPremium: plan.totalPremium ?? "",
        });
        if (features.length) {
          setIsExpanded((value) => !value);
        }
      }}
      type="button"
    >
      <div className="quote-plan-leading" aria-hidden="true">
        <ShieldCheck size={15} strokeWidth={2} />
      </div>
      <div className="quote-plan-body">
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
          {features.length ? (
            <span className="quote-plan-expand-indicator">
              <span>{isExpanded ? "Hide details" : "Show details"}</span>
              <ChevronDown
                className={isExpanded ? "is-expanded" : ""}
                size={15}
                strokeWidth={2}
              />
            </span>
          ) : null}
        </div>
        <div
          className={`quote-plan-details${isExpanded ? " is-expanded" : ""}`}
          id={detailsId}
        >
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
        </div>
      </div>
    </button>
  );
}
