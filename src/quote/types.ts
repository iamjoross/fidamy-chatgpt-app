export type BillingPeriod = "monthly" | "yearly";
export type CaptureStep = "idle" | "awaiting_first_name";

export type Labels = {
  en?: string;
  nl?: string;
};

export type Feature = {
  code?: string;
  labels?: Labels;
};

export type Plan = {
  plan?: string;
  labels?: Labels;
  totalPremium?: string | number;
  deductibleAmount?: string | number;
  features?: Feature[];
};

export type Quotation = {
  monthly?: Plan[];
  yearly?: Plan[];
  insurable?: boolean;
  totalPremium?: string | number;
};

export type IntentOutput = {
  message?: string;
  url?: string;
};

export type WidgetProps = {
  deviceCategory?: string;
  deviceMarketValue?: number;
  quotation?: Quotation;
  intentUrl?: string;
  intent?: IntentOutput;
};

export type SelectionState = {
  selectedPlanId: string;
  selectedPlanLabel: string;
  selectedBillingPeriod: BillingPeriod | "";
  selectedPremium: string | number;
  captureStep: CaptureStep;
};

export type PlanSelection = {
  billingPeriod: BillingPeriod;
  id: string;
  label: string;
  totalPremium: string | number;
};

export type CapturePromptInput = {
  selectedPlanLabel: string;
  selectedBillingPeriod: string;
  selectedPremium: string | number;
  deviceCategory: string;
  deviceMarketValue: string | number;
};
