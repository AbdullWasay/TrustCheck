import { useEffect, useState } from "react";

import { clearStoredUser, getStoredUser } from "./lib/api";
import Login from "./pages/Login";
import SellerCheck from "./pages/SellerCheck";
import SellerDetails from "./pages/SellerDetails";
import TrustSnapshot from "./pages/TrustSnapshot";
import Evidence from "./pages/Evidence";
import DecisionSummary from "./pages/DecisionSummary";

function App() {
  const [screen, setScreen] = useState("login");
  const [user, setUser] = useState(null);
  const [activeCheck, setActiveCheck] = useState(null);

  useEffect(() => {
    const stored = getStoredUser();
    if (stored?.id) {
      setUser(stored);
      setScreen("seller-check");
    }
  }, []);

  const handleLogin = (loggedInUser) => {
    setUser(loggedInUser);
    setActiveCheck(null);
    setScreen("seller-check");
  };

  const handleLogout = () => {
    clearStoredUser();
    setUser(null);
    setActiveCheck(null);
    setScreen("login");
  };

  const handleSellerCheck = (check) => {
    setActiveCheck(check);
    setScreen("seller-details");
  };

  const handleSellerDetails = (check) => {
    setActiveCheck(check);
    setScreen("trust-snapshot");
  };

  const handleEvidence = () => {
    setScreen("evidence");
  };

  const handleDecision = () => {
    setScreen("decision");
  };

  const handleRestart = () => {
    setActiveCheck(null);
    setScreen("seller-check");
  };

  if (screen === "login") {
    return <Login onLogin={handleLogin} />;
  }

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  if (screen === "seller-check") {
    return (
      <SellerCheck
        user={user}
        onContinue={handleSellerCheck}
        onLogout={handleLogout}
      />
    );
  }

  if (screen === "seller-details") {
    return (
      <SellerDetails
        user={user}
        check={activeCheck}
        onContinue={handleSellerDetails}
      />
    );
  }

  if (screen === "trust-snapshot") {
    return (
      <TrustSnapshot
        check={activeCheck}
        onContinue={handleEvidence}
      />
    );
  }

  if (screen === "evidence") {
    return <Evidence check={activeCheck} onContinue={handleDecision} />;
  }

  if (screen === "decision") {
    return (
      <DecisionSummary
        check={activeCheck}
        onRestart={handleRestart}
        onLogout={handleLogout}
      />
    );
  }

  return null;
}

export default App;
