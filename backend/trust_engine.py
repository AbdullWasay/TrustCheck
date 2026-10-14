"""Trust scoring used by the Python backend before saving results to Supabase."""


def assess_seller(payload: dict) -> dict:
    website = (payload.get("website") or "").strip().lower()
    phone = (payload.get("phone") or "").strip()
    seller_type = payload.get("seller_type") or ""
    seller_name = payload.get("seller_name") or "the seller"
    payment_method = payload.get("payment_method") or ""
    return_policy = payload.get("return_policy") or ""

    positive = []
    warnings = []

    if website.startswith("https://"):
        positive.append("HTTPS/security appears to be enabled on the seller link.")
    elif website.startswith("http://"):
        warnings.append("Seller link does not use HTTPS.")
    else:
        warnings.append("Seller website/profile format looks incomplete.")

    if phone and len("".join(ch for ch in phone if ch.isdigit())) >= 10:
        positive.append("Seller contact phone number was provided.")
    else:
        warnings.append("Seller phone number looks incomplete.")

    if seller_type in {"Independent Website", "Instagram", "Facebook"}:
        positive.append(f"Seller type identified as {seller_type}.")
    else:
        warnings.append("Seller operates mainly through informal messaging channels.")

    if return_policy == "Yes":
        positive.append("A clear return/refund policy was reported.")
    elif return_policy == "No":
        warnings.append("No clear return or refund policy.")
    else:
        warnings.append("Return/refund policy is unclear.")

    if payment_method == "Cash on Delivery":
        positive.append("Cash on Delivery reduces advance-payment risk.")
    elif payment_method in {"Credit/Debit Card"}:
        positive.append("Card payment may offer stronger buyer protection.")
    elif payment_method in {"Bank Transfer", "JazzCash", "EasyPaisa"}:
        warnings.append("Advance payment is requested before delivery.")
    else:
        warnings.append("Payment method needs careful review.")

    warning_count = len(warnings)
    positive_count = len(positive)

    if warning_count == 0 and positive_count >= 3:
        risk_level = "LOW RISK"
        decision = "LIKELY SAFE TO PROCEED"
        summary = (
            f"Most available signals for {seller_name} look positive. "
            "Still keep records of the conversation before paying."
        )
    elif warning_count >= 3 or (warning_count >= 2 and positive_count <= 1):
        risk_level = "HIGH RISK"
        decision = "AVOID OR VERIFY FIRST"
        summary = (
            f"Several warning signals were found for {seller_name}. "
            "Verify the seller carefully before sending any payment."
        )
    else:
        risk_level = "MEDIUM RISK"
        decision = "PROCEED WITH CAUTION"
        summary = (
            f"The available information for {seller_name} contains both positive "
            "and warning signals. Review the evidence carefully before payment."
        )

    checklist = [
        "Verify the seller's identity.",
        "Review return and refund conditions.",
        "Avoid unsafe payment methods.",
        "Keep records of seller conversations.",
        "Start with a small test order if unsure.",
    ]

    return {
        "risk_level": risk_level,
        "decision": decision,
        "positive_signals": positive,
        "warning_signals": warnings,
        "checklist": checklist,
        "summary": summary,
    }
