import { useEffect, useState } from "react";
import CustomButton from "../components/CustomButton";
import CustomInput from "../components/CustomInput";
import FormSection from "../components/FormSection";
import { api } from "../lib/api";

function SellerCheck({ user, onContinue, onLogout }) {
  const [website, setWebsite] = useState("");
  const [phone, setPhone] = useState("");
  const [sellerType, setSellerType] = useState("Instagram");
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      setLoadingHistory(true);
      try {
        const data = await api.listChecks(user.id);
        if (!cancelled) {
          setHistory(data.checks || []);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || "Could not load previous checks.");
        }
      } finally {
        if (!cancelled) {
          setLoadingHistory(false);
        }
      }
    }

    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [user.id]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await api.startCheck(user.id, {
        website: website.trim(),
        phone: phone.trim(),
        seller_type: sellerType,
      });
      onContinue(data.check);
    } catch (err) {
      setError(err.message || "Could not save seller check.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="content-card">
        <div className="top-row">
          <span className="step-label">STEP 1 OF 4</span>
          <button type="button" className="link-button" onClick={onLogout}>
            Logout
          </button>
        </div>

        <h1>Check a Seller</h1>

        <p className="subtitle">
          Enter the information you have about the seller.
        </p>

        <form onSubmit={handleSubmit}>
          <FormSection
            title="Seller Information"
            description="Provide at least the seller website and phone number."
          >
            <CustomInput
              label="Seller Website or Social Profile"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              placeholder="https://instagram.com/example"
              required
            />

            <div className="input-group">
              <label>Seller Type</label>

              <select
                value={sellerType}
                onChange={(e) => setSellerType(e.target.value)}
              >
                <option>Instagram</option>
                <option>Facebook</option>
                <option>WhatsApp</option>
                <option>Independent Website</option>
              </select>
            </div>

            <CustomInput
              label="Phone Number"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="0300-1234567"
              required
            />

            {error && <p className="input-error">{error}</p>}

            <CustomButton type="submit" disabled={loading}>
              {loading ? "Saving..." : "Continue"}
            </CustomButton>
          </FormSection>
        </form>

        <FormSection
          title="Your Recent Checks"
          description="Previous seller checks linked to your account."
        >
          {loadingHistory && <p className="muted">Loading history...</p>}

          {!loadingHistory && history.length === 0 && (
            <p className="muted">No previous checks yet.</p>
          )}

          {!loadingHistory &&
            history.slice(0, 5).map((item) => (
              <div className="history-item" key={item.id}>
                <strong>{item.seller_name || "Draft check"}</strong>
                <span>
                  {item.website} · {item.risk_level || "In progress"}
                </span>
              </div>
            ))}
        </FormSection>
      </div>
    </div>
  );
}

export default SellerCheck;
