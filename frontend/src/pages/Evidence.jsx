import CustomButton from "../components/CustomButton";
import FormSection from "../components/FormSection";

function Evidence({ check, onContinue }) {
  return (
    <div className="page">
      <div className="content-card">
        <span className="step-label">STEP 4 OF 4</span>

        <h1>Evidence & Safer Purchase Checklist</h1>

        <FormSection
          title="Positive Signals"
          description="Signals that may support greater confidence."
        >
          <ul className="evidence-list positive-list">
            {(check?.positive_signals || ["No positive signals recorded."]).map(
              (item) => (
                <li key={item}>{item}</li>
              ),
            )}
          </ul>
        </FormSection>

        <FormSection
          title="Warning Signals"
          description="Signals that should be reviewed carefully."
        >
          <ul className="evidence-list warning-list">
            {(check?.warning_signals || ["No warning signals recorded."]).map(
              (item) => (
                <li key={item}>{item}</li>
              ),
            )}
          </ul>
        </FormSection>

        <FormSection
          title="Before You Pay"
          description="Use these checks before making your final decision."
        >
          <ul className="evidence-list">
            {(check?.checklist || []).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </FormSection>

        <CustomButton onClick={onContinue}>View Decision Summary</CustomButton>
      </div>
    </div>
  );
}

export default Evidence;
