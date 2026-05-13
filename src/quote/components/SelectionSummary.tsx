import { formatAmount } from "../utils";
import type { SelectionState } from "../types";

type SelectionSummaryProps = {
  selection: SelectionState;
};

export function SelectionSummary({
  selection,
}: SelectionSummaryProps) {
  return (
    <section className="quote-selection-summary">
      <div className="quote-selection-copy">
        <span className="quote-selection-kicker">Selected plan</span>
        <strong>
          {selection.selectedPlanLabel} {selection.selectedBillingPeriod} plan
        </strong>
        <p>Continue in chat and upload your receipt if you have one.</p>
      </div>
      <div className="quote-selection-actions">
        <div className="quote-selection-price">
          {formatAmount(selection.selectedPremium)}
        </div>
      </div>
    </section>
  );
}
