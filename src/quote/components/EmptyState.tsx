import { Smartphone } from "lucide-react";

export function EmptyState() {
  return (
    <section className="quote-empty-state">
      <Smartphone size={22} strokeWidth={1.8} />
      <div>
        <h2>No coverage options available</h2>
        <p>
          This quote did not return monthly or yearly plans for this device.
        </p>
      </div>
    </section>
  );
}
