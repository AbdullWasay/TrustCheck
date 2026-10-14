import CustomButton from "../components/CustomButton";
import FormSection from "../components/FormSection";

function DecisionSummary({ check, onRestart, onLogout }) {
  return (
    <div className="page">
      <div className="content-card final-card">
        <div className="success-icon">✓</div>

        <span className="step-label">CHECK COMPLETE</span>

        <h1>Decision Support Summary</h1>

        <div className="decision-box">
          <p>Suggested next step</p>
          <h2>{check?.decision || "PROCEED WITH CAUTION"}</h2>
        </div>

        <FormSection
          title="What This Means"
          description="TrustCheck PK provides decision support, not a guarantee."
        >
          <p>
            {check?.summary ||
              "The available information contains both positive and warning signals. Review the evidence carefully before sending payment to the seller."}
          </p>
        </FormSection>

        <CustomButton onClick={onRestart}>Start Another Check</CustomButton>

        <button type="button" className="link-button" onClick={onLogout}>
          Logout
        </button>
      </div>
    </div>
  );
}

export default DecisionSummary;
