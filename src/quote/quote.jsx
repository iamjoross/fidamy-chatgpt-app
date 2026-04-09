import "./quote.css";

import { CheckCircle2, Shield, Smartphone, WalletCards } from "lucide-react";

import { useOpenAiGlobal } from "../use-openai-global";
import { useWidgetState } from "../use-widget-state";
import { useWidgetProps } from "../use-widget-props";

function formatAmount(amount) {
  const numericAmount = Number.parseFloat(String(amount ?? ""));
  if (Number.isNaN(numericAmount)) {
    return String(amount ?? "-");
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numericAmount);
}

function formatPlanName(value) {
  return String(value ?? "")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatCategoryLabel(value) {
  if (!value) {
    return "Device";
  }

  return String(value).replace(/[_-]+/g, " ");
}

function planId(billingPeriod, plan) {
  return `${billingPeriod}:${plan?.plan || "unknown"}`;
}

function PlanCard({ billingPeriod, plan, isSelected, onSelect }) {
  const planLabel = plan?.labels?.en || formatPlanName(plan?.plan);
  const features = Array.isArray(plan?.features) ? plan.features : [];
  const selectionId = planId(billingPeriod, plan);

  return (
    <button
      aria-pressed={isSelected}
      className={`quote-plan-card${isSelected ? " is-selected" : ""}`}
      onClick={() =>
        onSelect({
          billingPeriod,
          id: selectionId,
          label: planLabel,
          totalPremium: plan?.totalPremium || "",
        })
      }
      type="button"
    >
      <div className="quote-plan-header">
        <div>
          <p className="quote-plan-kicker">{plan?.plan || "plan"}</p>
          <h3>{planLabel}</h3>
        </div>
        <div className="quote-plan-price-wrap">
          {isSelected ? (
            <span className="quote-plan-selected-badge">
              <CheckCircle2 size={15} strokeWidth={2} />
              Selected
            </span>
          ) : null}
          <div className="quote-plan-price">{formatAmount(plan?.totalPremium)}</div>
        </div>
      </div>
      <ul className="quote-feature-list">
        {features.map((feature) => (
          <li key={feature.code || feature.labels?.en}>
            {feature.labels?.en || formatPlanName(feature.code)}
          </li>
        ))}
      </ul>
    </button>
  );
}

function PlanGroup({ title, icon: Icon, plans, billingPeriod, selectedId, onSelect }) {
  if (!plans.length) {
    return null;
  }

  return (
    <section className="quote-group">
      <div className="quote-group-header">
        <div className="quote-group-icon">
          <Icon size={16} strokeWidth={1.8} />
        </div>
        <div>
          <p className="quote-group-kicker">Coverage options</p>
          <h2>{title}</h2>
        </div>
      </div>
      <div className="quote-plan-grid">
        {plans.map((plan) => (
          <PlanCard
            key={`${title}-${plan.plan}`}
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

export function App() {
  const rawToolOutput = useOpenAiGlobal("toolOutput");
  const [selection, setSelection] = useWidgetState({
    selectedPlanId: "",
    selectedPlanLabel: "",
    selectedBillingPeriod: "",
    selectedPremium: "",
  });
  const {
    deviceCategory = "",
    deviceMarketValue = 0,
    quotation = {},
  } = useWidgetProps({
    deviceCategory: "",
    deviceMarketValue: 0,
    quotation: {},
  });

  const monthlyPlans = Array.isArray(quotation?.monthly) ? quotation.monthly : [];
  const yearlyPlans = Array.isArray(quotation?.yearly) ? quotation.yearly : [];
  const isLoading = rawToolOutput == null;
  const isInsurable = quotation?.insurable === true;
  const totalPremium = quotation?.totalPremium;
  const hasPlans = monthlyPlans.length > 0 || yearlyPlans.length > 0;
  const selectedPlanId = selection?.selectedPlanId || "";
  const statusLabel = isLoading
    ? "Fetching quote"
    : isInsurable
      ? "Insurable"
      : "Unavailable";
  const premiumLabel = isLoading ? "Calculating..." : formatAmount(totalPremium);

  const handleSelectPlan = (nextSelection) => {
    setSelection({
      selectedPlanId: nextSelection.id,
      selectedPlanLabel: nextSelection.label,
      selectedBillingPeriod: nextSelection.billingPeriod,
      selectedPremium: nextSelection.totalPremium,
    });
  };

  return (
    <div className="quote-widget-shell">
      <div className="quote-widget-card">
        <header className="quote-summary">
          <div className="quote-summary-copy">
            <div className="quote-badge">
              <Shield size={16} strokeWidth={1.8} />
              Extended warranty quotation
            </div>
            <h1>Choose a protection plan</h1>
            <p>Compare available monthly and yearly coverage for your device.</p>
          </div>
          <div className="quote-summary-metrics">
            <div className="quote-status-pill">
              <span className="quote-status-label">Status</span>
              <strong
                className={`quote-status-value ${
                  isLoading
                    ? "is-loading"
                    : isInsurable
                      ? "is-insurable"
                      : "is-unavailable"
                }`}
              >
                {statusLabel}
              </strong>
            </div>
          </div>
        </header>

        <section className="quote-facts">
          <div className="quote-fact">
            <span>Category</span>
            <strong>{formatCategoryLabel(deviceCategory)}</strong>
          </div>
          <div className="quote-fact">
            <span>Market value</span>
            <strong>{formatAmount(deviceMarketValue)}</strong>
          </div>
          <div className="quote-fact">
            <span>Starting from</span>
            <strong>{premiumLabel}</strong>
          </div>
        </section>

        {!isLoading && selection?.selectedPlanId ? (
          <section className="quote-selection-summary">
            <div className="quote-selection-copy">
              <span className="quote-selection-kicker">Selected plan</span>
              <strong>
                {selection.selectedPlanLabel} {selection.selectedBillingPeriod} plan
              </strong>
              <p>Review your choice and continue when you are ready.</p>
            </div>
            <div className="quote-selection-actions">
              <div className="quote-selection-price">
                {formatAmount(selection.selectedPremium)}
              </div>
              <button className="quote-proceed-button" type="button">
                Choose plan
              </button>
            </div>
          </section>
        ) : null}

        {isLoading ? (
          <section className="quote-loading-state">
            <div className="quote-loading-copy">
              <div className="quote-loading-badge">
                <Shield size={18} strokeWidth={1.8} />
                Fetching live quote
              </div>
              <h2>Checking available coverage options.</h2>
              <p>This usually takes a moment.</p>
            </div>
            <div
              aria-busy="true"
              aria-label="Loading quotation"
              aria-valuemax={100}
              aria-valuemin={0}
              className="quote-progress"
              role="progressbar"
            >
              <div className="quote-progress-bar" />
            </div>
            <div aria-hidden="true" className="quote-loading-grid">
              <div className="quote-loading-card" />
              <div className="quote-loading-card" />
            </div>
          </section>
        ) : !hasPlans ? (
          <section className="quote-empty-state">
            <Smartphone size={22} strokeWidth={1.8} />
            <div>
              <h2>No coverage options available</h2>
              <p>This quote did not return monthly or yearly plans for this device.</p>
            </div>
          </section>
        ) : (
          <div className="quote-groups">
            <PlanGroup
              billingPeriod="monthly"
              icon={Smartphone}
              onSelect={handleSelectPlan}
              plans={monthlyPlans}
              selectedId={selectedPlanId}
              title="Monthly plans"
            />
            <PlanGroup
              billingPeriod="yearly"
              icon={WalletCards}
              onSelect={handleSelectPlan}
              plans={yearlyPlans}
              selectedId={selectedPlanId}
              title="Yearly plans"
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
