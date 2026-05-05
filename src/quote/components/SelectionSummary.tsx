import type { SelectionState } from "../types";
import { formatAmount } from "../utils";

type SelectionSummaryProps = {
  selection: SelectionState;
  isAwaitingFirstName: boolean;
  onChoosePlan: () => Promise<void>;
};

export function SelectionSummary({
  selection,
  isAwaitingFirstName,
  onChoosePlan,
}: SelectionSummaryProps) {
  return (
    <section className="quote-selection-summary">
      <div className="quote-selection-copy">
        <span className="quote-selection-kicker">Selected plan</span>
        <strong>
          {selection.selectedPlanLabel} {selection.selectedBillingPeriod} plan
        </strong>
        <p>
          {isAwaitingFirstName
            ? "Continue in chat to provide your first and last name."
            : "Review your choice and continue when you are ready."}
        </p>
      </div>
      <div className="quote-selection-actions">
        <div className="quote-selection-price">
          {formatAmount(selection.selectedPremium)}
        </div>
        {isAwaitingFirstName ? (
          <div className="quote-followup-state">
            Continue in chat to provide your first and last name
          </div>
        ) : (
          <button
            className="quote-proceed-button"
            onClick={() => {
              void onChoosePlan();
            }}
            type="button"
          >
            Choose plan
          </button>
        )}
      </div>
    </section>
  );
}
