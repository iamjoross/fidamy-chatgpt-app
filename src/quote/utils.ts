import type { BillingPeriod, Plan, CapturePromptInput } from "./types";

export function formatAmount(amount: string | number | undefined): string {
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

export function formatPlanName(value: string | undefined): string {
  return String(value ?? "")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function formatCategoryLabel(value: string | undefined): string {
  if (!value) {
    return "Device";
  }

  return String(value).replace(/[_-]+/g, " ");
}

export function planId(billingPeriod: BillingPeriod, plan: Plan): string {
  return `${billingPeriod}:${plan.plan ?? "unknown"}`;
}

export function buildCapturePrompt(selection: CapturePromptInput): string {
  const deviceMarketValue = formatAmount(selection.deviceMarketValue);

  return (
    "The user selected the " +
    `${selection.selectedPlanLabel} ${selection.selectedBillingPeriod} ` +
    `plan at ${formatAmount(selection.selectedPremium)}. ` +
    `The quoted device market value is ${deviceMarketValue}. ` +
    "First ask the user whether they have a receipt for the purchased item. If they have a receipt, ask them to upload the receipt image or document in chat before collecting details. Use ChatGPT vision/OCR on the uploaded receipt to extract any visible applicant name, email, phone, address, device brand, device model, serial number, IMEI, purchase price/current value, and purchase evidence. " +
    "After OCR, briefly summarize only the extracted fields you intend to use and ask the user to confirm or correct them before treating them as collected values. Do not expose unnecessary raw OCR text. If a field is unclear or sensitive and not confidently readable, do not guess; ask the user for that field directly. If the receipt purchase price or value differs from the quoted device market value, ask the user to confirm the correct current market value before submitting; do not silently change the selected plan or selected premium. " +
    "If the user does not have a receipt, continue with manual collection. In all cases, collect only missing or invalid required details one by one, asking only one question per assistant message and waiting for the user's answer before asking the next field. If the user seems unsure about buying, do not collect details and offer to help them compare the available packages. " +
    "Use soft-rotation phrasing for questions: rotate among a small set of polite openings and avoid repeating the exact same opening pattern in consecutive turns. " +
    "Examples of acceptable openings to rotate: 'Could you share ...', 'May I have ...', 'Please provide ...', 'What is ...'. " +
    "Validate each value immediately after the user provides it. If a value is invalid, explain briefly what is wrong and ask for the same field again; do not continue to the next field until valid. " +
    "Infer deviceBrand from the conversation whenever it is obvious (for example: iPhone -> Apple, Galaxy -> Samsung, Pixel -> Google) and inject that inferred value directly in the final tool arguments. Only ask the user for device brand if it cannot be inferred confidently. " +
    "Validation rules: email must be valid; phone number must be E.164 with country code (example +31612345678); extract phoneCountryCode and phoneNo from the validated phone number; date of birth must be dd-mm-yyyy and in the past; IMEI must be 15 digits; serial number must be at least 5 characters; at least one of serialNumber or imei is required. " +
    "Guardrails: do not ask multiple fields in one message, do not skip fields, and do not change any required formats. " +
    "Use this exact order: first name, last name, email, phone number including country code, date of birth (dd-mm-yyyy), street, house number, zip code, city, country of residence, device brand (if not inferable), device model, then either serial number or IMEI. " +
    "When OCR or earlier conversation already supplied a confirmed value for a field in that order, skip asking for that field and continue to the next missing field. " +
    "After collecting all values, call the MCP tool " +
    "`capture-applicant-values` with arguments: " +
    "{ firstName, lastName, email, phoneNumber, phoneCountryCode, phoneNo, dateOfBirth, street, houseNumber, " +
    "zipCode, city, countryOfResidence, deviceBrand, deviceModel, serialNumber?, imei?, " +
    `deviceCategory: "${selection.deviceCategory}", ` +
    `deviceMarketValue: "${selection.deviceMarketValue}", ` +
    `selectedPlanLabel: "${selection.selectedPlanLabel}", ` +
    `selectedBillingPeriod: "${selection.selectedBillingPeriod}", ` +
    `selectedPremium: "${formatAmount(selection.selectedPremium)}" }. ` +
    "After the tool returns, respond to the user with the exact checkout URL from the tool response (`url` or `intentUrl`) and do not omit it."
  );
}
