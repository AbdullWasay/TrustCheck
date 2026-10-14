import CustomButton from "../components/CustomButton";
import FormSection from "../components/FormSection";

function TrustSnapshot({ check, onContinue }) {
  const risk = check?.risk_level || "MEDIUM RISK";
  const riskClass =
    risk.includes("HIGH")
      ? "risk-card high"
      : risk.includes("LOW")
        ? "risk-card low"
        : "risk-card";

  return (
    <div className="page">
      <div className="content-card">
        <span className="step-label">STEP 3 OF 4</span>

        <h1>Trust Snapshot</h1>

        <div className={riskClass}>
          <p className="risk-label">POTENTIAL RISK</p>

          <h2>{risk}</h2>

          <p>
            {check?.summary ||
              "Some positive signals were found, but there are also warning signs that should be reviewed before payment."}
          </p>
        </div>

        <FormSection
          title="Check Summary"
          description={`Assessment for ${check?.seller_name || "the seller"}.`}
        >
          {(check?.positive_signals || []).map((signal) => (
            <div className="signal-row positive" key={signal}>
              <span>✓</span>
              <span>{signal}</span>
            </div>
          ))}

          {(check?.warning_signals || []).map((signal) => (
            <div className="signal-row warning" key={signal}>
              <span>!</span>
              <span>{signal}</span>
            </div>
          ))}
        </FormSection>

        <CustomButton onClick={onContinue}>View Evidence</CustomButton>
      </div>
    </div>
  );
}

export default TrustSnapshot;
