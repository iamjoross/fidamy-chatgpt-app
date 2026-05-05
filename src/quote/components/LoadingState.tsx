import { ShieldCheck } from "lucide-react";

export function LoadingState() {
  return (
    <section className="quote-loading-state">
      <div className="quote-group-header">
        <div className="quote-group-icon">
          <ShieldCheck size={16} strokeWidth={1.8} />
        </div>
        <div>
          <h2>Checking available coverage</h2>
        </div>
      </div>
      <div
        aria-busy="true"
        aria-label="Loading quotation"
        className="quote-loading-list"
        role="status"
      >
        <div className="quote-loading-row">
          <div className="quote-loading-icon" />
          <div className="quote-loading-lines">
            <div className="quote-loading-line is-title" />
            <div className="quote-loading-line is-price" />
            <div className="quote-loading-line" />
          </div>
        </div>
        <div className="quote-loading-row">
          <div className="quote-loading-icon" />
          <div className="quote-loading-lines">
            <div className="quote-loading-line is-title" />
            <div className="quote-loading-line is-price" />
            <div className="quote-loading-line" />
          </div>
        </div>
      </div>
    </section>
  );
}
