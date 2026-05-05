import type { SelectionState, WidgetProps } from "./types";

export const DEFAULT_WIDGET_PROPS: WidgetProps = {
  deviceCategory: "",
  deviceMarketValue: 0,
  quotation: {},
  intentUrl: "",
  intent: {},
};

export const DEV_MOCK_WIDGET_PROPS: WidgetProps = {
  deviceCategory: "Smartphone",
  deviceMarketValue: 1299,
  quotation: {
    insurable: true,
    monthly: [
      {
        plan: "basic",
        labels: {
          en: "Basic",
          nl: "Basis",
        },
        totalPremium: "17.75",
        deductibleAmount: "50.00",
        features: [
          {
            code: "fall_impact",
            labels: {
              en: "Fall & impact damage",
              nl: "Val- en impactschade",
            },
          },
          {
            code: "screen_breakage",
            labels: {
              en: "Screen breakage",
              nl: "Schermbreuk",
            },
          },
        ],
      },
      {
        plan: "extended",
        labels: {
          en: "Extended",
          nl: "Uitgebreid",
        },
        totalPremium: "22.98",
        deductibleAmount: "100.00",
        features: [
          {
            code: "theft",
            labels: {
              en: "Theft of the device",
              nl: "Diefstal van het toestel",
            },
          },
          {
            code: "pickpocketing",
            labels: {
              en: "Pickpocketing",
              nl: "Zakkenrollerij",
            },
          },
          {
            code: "robbery",
            labels: {
              en: "Robbery",
              nl: "Beroving",
            },
          },
        ],
      },
    ],
    yearly: [
      {
        plan: "basic",
        labels: {
          en: "Basic",
          nl: "Basis",
        },
        totalPremium: "201.32",
        deductibleAmount: "50.00",
        features: [
          {
            code: "fall_impact",
            labels: {
              en: "Fall & impact damage",
              nl: "Val- en impactschade",
            },
          },
          {
            code: "screen_breakage",
            labels: {
              en: "Screen breakage",
              nl: "Schermbreuk",
            },
          },
        ],
      },
      {
        plan: "extended",
        labels: {
          en: "Extended",
          nl: "Uitgebreid",
        },
        totalPremium: "261.14",
        deductibleAmount: "100.00",
        features: [
          {
            code: "theft",
            labels: {
              en: "Theft of the device",
              nl: "Diefstal van het toestel",
            },
          },
          {
            code: "pickpocketing",
            labels: {
              en: "Pickpocketing",
              nl: "Zakkenrollerij",
            },
          },
          {
            code: "robbery",
            labels: {
              en: "Robbery",
              nl: "Beroving",
            },
          },
        ],
      },
    ],
    totalPremium: "17.75",
  },
  intentUrl: "https://example.com/checkout",
  intent: { url: "https://example.com/checkout" },
};

export const DEFAULT_SELECTION_STATE: SelectionState = {
  selectedPlanId: "",
  selectedPlanLabel: "",
  selectedBillingPeriod: "",
  selectedPremium: "",
  captureStep: "idle",
};
