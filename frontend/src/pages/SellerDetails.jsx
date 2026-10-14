import { useState } from "react";
import CustomButton from "../components/CustomButton";
import CustomInput from "../components/CustomInput";
import FormSection from "../components/FormSection";
import { api } from "../lib/api";
import { validateSellerName } from "../lib/validation";

function SellerDetails({ user, check, onContinue }) {
  const [sellerName, setSellerName] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("Bank Transfer");
  const [returnPolicy, setReturnPolicy] = useState("No");
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const validateForm = () => {
    const nextErrors = {
      sellerName: validateSellerName(sellerName),
    };
    setFieldErrors(nextErrors);
    return !Object.values(nextErrors).some(Boolean);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (!validateForm()) return;

    setLoading(true);

    try {
      const data = await api.updateDetails(user.id, check.id, {
        seller_name: sellerName.trim(),
        payment_method: paymentMethod,
        return_policy: returnPolicy,
      });
      onContinue(data.check);
    } catch (err) {
      setError(err.message || "Could not save seller details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="content-card">
        <span className="step-label">STEP 2 OF 4</span>

        <h1>Seller Details</h1>

        <p className="subtitle">
          Tell us a little more about {check?.website || "the seller"}.
        </p>

        <form onSubmit={handleSubmit} noValidate>
          <FormSection
            title="Business Information"
            description="These details help organise the trust assessment."
          >
            <CustomInput
              label="Seller or Business Name"
              value={sellerName}
              onChange={(e) => {
                setSellerName(e.target.value);
                setFieldErrors((prev) => ({ ...prev, sellerName: "" }));
              }}
              placeholder="Example Fashion Store"
              required
              error={fieldErrors.sellerName}
            />

            <div className="input-group">
              <label>Requested Payment Method</label>

              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
              >
                <option>Bank Transfer</option>
                <option>Cash on Delivery</option>
                <option>JazzCash</option>
                <option>EasyPaisa</option>
                <option>Credit/Debit Card</option>
              </select>
            </div>

            <div className="input-group">
              <label>Clear Return/Refund Policy?</label>

              <select
                value={returnPolicy}
                onChange={(e) => setReturnPolicy(e.target.value)}
              >
                <option>Yes</option>
                <option>No</option>
                <option>Not Sure</option>
              </select>
            </div>

            {error && <p className="input-error">{error}</p>}

            <CustomButton type="submit" disabled={loading}>
              {loading ? "Assessing..." : "Check Trust Signals"}
            </CustomButton>
          </FormSection>
        </form>
      </div>
    </div>
  );
}

export default SellerDetails;
