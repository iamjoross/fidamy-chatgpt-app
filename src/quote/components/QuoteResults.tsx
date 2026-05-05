import type { Plan, PlanSelection } from "../types";
import { BillingPeriodSection } from "./BillingPeriodSection";

type QuoteResultsProps = {
  monthlyPlans: Plan[];
  yearlyPlans: Plan[];
  selectedId: string;
  onSelect: (selection: PlanSelection) => void;
};

export function QuoteResults({
  monthlyPlans,
  yearlyPlans,
  selectedId,
  onSelect,
}: QuoteResultsProps) {
  return (
    <div className="quote-groups">
      <BillingPeriodSection
        billingPeriod="monthly"
        plans={monthlyPlans}
        selectedId={selectedId}
        onSelect={onSelect}
      />
      <BillingPeriodSection
        billingPeriod="yearly"
        plans={yearlyPlans}
        selectedId={selectedId}
        onSelect={onSelect}
      />
    </div>
  );
}
