import type { BillingPeriod, Plan } from "./types";

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
