import { Shield } from "lucide-react";

export function LoadingState() {
  return (
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
  );
}
