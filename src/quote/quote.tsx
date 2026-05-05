import "./quote.css";

import { useEffect, useState } from "react";
import { Shield } from "lucide-react";
import { buildCapturePrompt } from "./utils";

import { useOpenAiGlobal } from "../use-openai-global";
import { useWidgetProps } from "../use-widget-props";
import { useWidgetState } from "../use-widget-state";

import { SelectionSummary } from "./components/SelectionSummary";
import { LoadingState } from "./components/LoadingState";
import { EmptyState } from "./components/EmptyState";
import { QuoteResults } from "./components/QuoteResults";

import type { PlanSelection, SelectionState, WidgetProps } from "./types";
import {
  DEFAULT_WIDGET_PROPS,
  DEV_MOCK_WIDGET_PROPS,
  DEFAULT_SELECTION_STATE,
} from "./constants";
import { formatAmount, formatCategoryLabel } from "./utils";

export function App() {
  const rawToolOutput = useOpenAiGlobal("toolOutput");
  const [selectionState, setSelection] = useWidgetState<SelectionState>(
    DEFAULT_SELECTION_STATE,
  );
  const [devMockReady, setDevMockReady] = useState(() => !import.meta.env.DEV);

  useEffect(() => {
    if (!import.meta.env.DEV) {
      return;
    }

    const timeout = window.setTimeout(() => {
      setDevMockReady(true);
    }, 750);

    return () => window.clearTimeout(timeout);
  }, []);

  const selection = selectionState ?? DEFAULT_SELECTION_STATE;
  const hostWidgetProps = useWidgetProps<WidgetProps>(DEFAULT_WIDGET_PROPS);
  const hasOpenAiHost =
    typeof window !== "undefined" && typeof window.openai !== "undefined";

  const {
    deviceCategory = "",
    deviceMarketValue = 0,
    quotation = {},
    intentUrl = "",
    intent = {},
  } = import.meta.env.DEV && !hasOpenAiHost
    ? {
        ...DEFAULT_WIDGET_PROPS,
        ...DEV_MOCK_WIDGET_PROPS,
      }
    : hostWidgetProps;

  console.log("[quote-widget] intentUrl (top-level):", intentUrl);
  console.log("[quote-widget] intent.url (nested):", intent.url);
  const purchaseUrl = String(intentUrl || intent.url || "").trim();
  console.log("[quote-widget] resolved purchaseUrl:", purchaseUrl);

  const monthlyPlans = Array.isArray(quotation.monthly)
    ? quotation.monthly
    : [];
  const yearlyPlans = Array.isArray(quotation.yearly) ? quotation.yearly : [];
  const isLoading =
    import.meta.env.DEV && rawToolOutput == null
      ? !devMockReady
      : rawToolOutput == null;
  const hasPlans = monthlyPlans.length > 0 || yearlyPlans.length > 0;
  const selectedPlanId = selection.selectedPlanId;
  const isAwaitingFirstName = selection.captureStep === "awaiting_first_name";

  const handleSelectPlan = (nextSelection: PlanSelection) => {
    setSelection({
      selectedPlanId: nextSelection.id,
      selectedPlanLabel: nextSelection.label,
      selectedBillingPeriod: nextSelection.billingPeriod,
      selectedPremium: nextSelection.totalPremium,
      captureStep: "idle",
    });
  };

  const handleChoosePlan = async () => {
    if (!selection.selectedPlanId) {
      return;
    }

    if (!window.openai?.sendFollowUpMessage) {
      console.error("sendFollowUpMessage is not available in this context.");
      return;
    }

    try {
      await window.openai.sendFollowUpMessage({
        prompt: buildCapturePrompt({
          ...selection,
          deviceCategory,
          deviceMarketValue,
        }),
      });
      setSelection((prevState) => ({
        ...(prevState ?? DEFAULT_SELECTION_STATE),
        captureStep: "awaiting_first_name",
      }));
    } catch (error) {
      console.error(
        "Failed to continue conversation after plan selection:",
        error,
      );
    }
  };

  return (
    <div className="quote-widget-shell">
      <header className="quote-summary">
        <div className="quote-summary-copy">
          <div className="quote-badge">
            <Shield size={16} strokeWidth={1.8} />
            Review your coverage
          </div>
          <h1>
            Here are the insurance options for your{" "}
            {formatCategoryLabel(deviceCategory).toLowerCase()}(
            {formatAmount(deviceMarketValue)})
          </h1>
        </div>
        <div className="quote-summary-metrics">
          <div className="quote-facts">
            <div className="quote-fact">
              <span>Category</span>
              <strong>{formatCategoryLabel(deviceCategory)}</strong>
            </div>
          </div>
        </div>
      </header>

      {!isLoading && selectedPlanId ? (
        <SelectionSummary
          isAwaitingFirstName={isAwaitingFirstName}
          onChoosePlan={handleChoosePlan}
          selection={selection}
        />
      ) : null}

      {isLoading ? (
        <LoadingState />
      ) : !hasPlans ? (
        <EmptyState />
      ) : (
        <QuoteResults
          monthlyPlans={monthlyPlans}
          yearlyPlans={yearlyPlans}
          onSelect={handleSelectPlan}
          selectedId={selectedPlanId}
        />
      )}
    </div>
  );
}

export default App;
