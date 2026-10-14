import { useState } from "react";
import CustomButton from "../components/CustomButton";
import CustomInput from "../components/CustomInput";
import FormSection from "../components/FormSection";
import { api, storeUser } from "../lib/api";
import {
  validateEmail,
  validateFullName,
  validatePassword,
} from "../lib/validation";

function Login({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const validateForm = () => {
    const nextErrors = {
      email: validateEmail(email),
      password: validatePassword(password),
    };

    if (mode === "register") {
      nextErrors.fullName = validateFullName(fullName, { required: true });
    }

    setFieldErrors(nextErrors);
    return !Object.values(nextErrors).some(Boolean);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (!validateForm()) return;

    setLoading(true);

    try {
      const payload = {
        email: email.trim(),
        password,
        full_name: fullName.trim() || undefined,
      };

      const data =
        mode === "register"
          ? await api.register(payload)
          : await api.login(payload);

      storeUser(data.user);
      onLogin(data.user);
    } catch (err) {
      setError(err.message || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="login-card">
        <div className="logo-circle">TC</div>

        <h1>TrustCheck PK</h1>

        <p className="subtitle">Check the seller before you pay.</p>

        <form onSubmit={handleSubmit} noValidate>
          <FormSection
            title={mode === "login" ? "Welcome" : "Create Account"}
            description={
              mode === "login"
                ? "Sign in to start checking an online seller."
                : "Create an account to save and review your seller checks."
            }
          >
            {mode === "register" && (
              <CustomInput
                label="Full Name"
                value={fullName}
                onChange={(e) => {
                  setFullName(e.target.value);
                  setFieldErrors((prev) => ({ ...prev, fullName: "" }));
                }}
                placeholder="Your name"
                required
                error={fieldErrors.fullName}
              />
            )}

            <CustomInput
              label="Email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setFieldErrors((prev) => ({ ...prev, email: "" }));
              }}
              placeholder="Enter your email"
              required
              error={fieldErrors.email}
            />

            <CustomInput
              label="Password"
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setFieldErrors((prev) => ({ ...prev, password: "" }));
              }}
              placeholder="At least 6 characters"
              required
              error={fieldErrors.password}
            />

            {error && <p className="input-error">{error}</p>}

            <CustomButton type="submit" disabled={loading}>
              {loading
                ? "Please wait..."
                : mode === "login"
                  ? "Login"
                  : "Create Account"}
            </CustomButton>

            <button
              type="button"
              className="link-button"
              onClick={() => {
                setError("");
                setFieldErrors({});
                setMode(mode === "login" ? "register" : "login");
              }}
            >
              {mode === "login"
                ? "Need an account? Register"
                : "Already registered? Login"}
            </button>
          </FormSection>
        </form>
      </div>
    </div>
  );
}

export default Login;
