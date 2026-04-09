import "./quote.css";

import { CheckCircle2, Shield, Smartphone } from "lucide-react";

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

function PlanOptionCard({ billingPeriod, plan, isSelected, onSelect }) {
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
          <p className="quote-plan-kicker">{billingPeriod}</p>
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

function buildComparisonGroups(monthlyPlans, yearlyPlans) {
  const groups = new Map();

  for (const plan of monthlyPlans) {
    const key = plan?.plan || "unknown";
    groups.set(key, {
      key,
      label: plan?.labels?.en || formatPlanName(key),
      monthly: plan,
      yearly: null,
    });
  }

  for (const plan of yearlyPlans) {
    const key = plan?.plan || "unknown";
    const existing = groups.get(key);
    if (existing) {
      existing.yearly = plan;
    } else {
      groups.set(key, {
        key,
        label: plan?.labels?.en || formatPlanName(key),
        monthly: null,
        yearly: plan,
      });
    }
  }

  return Array.from(groups.values());
}

function ComparisonGroup({ group, selectedId, onSelect }) {
  if (!group.monthly && !group.yearly) {
    return null;
  }

  return (
    <section className="quote-group">
      <div className="quote-group-header">
        <div className="quote-group-icon">
          <Shield size={16} strokeWidth={1.8} />
        </div>
        <div>
          <p className="quote-group-kicker">Plan type</p>
          <h2>{group.label}</h2>
        </div>
      </div>
      <div className="quote-plan-grid">
        {group.monthly ? (
          <PlanOptionCard
            billingPeriod="monthly"
            isSelected={selectedId === planId("monthly", group.monthly)}
            onSelect={onSelect}
            plan={group.monthly}
          />
        ) : null}
        {group.yearly ? (
          <PlanOptionCard
            billingPeriod="yearly"
            isSelected={selectedId === planId("yearly", group.yearly)}
            onSelect={onSelect}
            plan={group.yearly}
          />
        ) : null}
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
    captureStep: "idle",
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
  const comparisonGroups = buildComparisonGroups(monthlyPlans, yearlyPlans);
  const isLoading = rawToolOutput == null;
  const isInsurable = quotation?.insurable === true;
  const totalPremium = quotation?.totalPremium;
  const hasPlans = comparisonGroups.length > 0;
  const selectedPlanId = selection?.selectedPlanId || "";
  const captureStep = selection?.captureStep || "idle";
  const isAwaitingFirstName = captureStep === "awaiting_first_name";
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
      captureStep: "idle",
    });
  };

  const handleChoosePlan = async () => {
    if (!selection?.selectedPlanId) {
      return;
    }

    if (!window.openai?.sendFollowUpMessage) {
      console.error("sendFollowUpMessage is not available in this context.");
      return;
    }

    try {
      await window.openai.sendFollowUpMessage({
        prompt: (
          "The user selected the "
          + `${selection.selectedPlanLabel} ${selection.selectedBillingPeriod} `
          + `plan at ${formatAmount(selection.selectedPremium)}. `
          + "Please capture these values conversationally: first name, last name, email, "
          + "phone number including country code, date of birth (dd-mm-yyyy), street, "
          + "house number, zip code, city, country of residence, device brand, and either serial number or IMEI. "
          + "After collecting all values, call the MCP tool "
          + "`capture-applicant-values` with arguments: "
          + "{ firstName, lastName, email, phoneNumber, dateOfBirth, street, houseNumber, "
          + "zipCode, city, countryOfResidence, deviceBrand, serialNumber?, imei?, "
          + `selectedPlanLabel: "${selection.selectedPlanLabel}", `
          + `selectedBillingPeriod: "${selection.selectedBillingPeriod}", `
          + `selectedPremium: "${formatAmount(selection.selectedPremium)}" }.`
        ),
      });
      setSelection((prevState) => ({
        ...(prevState ?? {}),
        captureStep: "awaiting_first_name",
      }));
    } catch (error) {
      console.error("Failed to continue conversation after plan selection:", error);
    }
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
            <h1>
              Here are the insurance options for your{" "}
              {formatCategoryLabel(deviceCategory).toLowerCase()} worth{" "}
              {formatAmount(deviceMarketValue)}
            </h1>
            <p>Compare available monthly and yearly coverage, then choose a plan.</p>
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
                <div className="quote-followup-state">Continue in chat to provide your first and last name</div>
              ) : (
                <button
                  className="quote-proceed-button"
                  onClick={handleChoosePlan}
                  type="button"
                >
                  Choose plan
                </button>
              )}
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
            {comparisonGroups.map((group) => (
              <ComparisonGroup
                group={group}
                key={group.key}
                onSelect={handleSelectPlan}
                selectedId={selectedPlanId}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
