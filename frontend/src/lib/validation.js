const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/i;

// Pakistan mobile: 03XXXXXXXXX, 03XX-XXXXXXX, +923XXXXXXXXX, 00923XXXXXXXXX
const PK_PHONE_PATTERN =
  /^(?:\+92|0092|0)?3\d{2}[-\s]?\d{7}$/;

export function validateEmail(value) {
  const email = value.trim();
  if (!email) return "Email is required.";
  if (!EMAIL_PATTERN.test(email)) return "Enter a valid email address.";
  return "";
}

export function validatePassword(value) {
  if (!value) return "Password is required.";
  if (value.length < 6) return "Password must be at least 6 characters.";
  return "";
}

export function validateFullName(value, { required = false } = {}) {
  const name = value.trim();
  if (!name) {
    return required ? "Full name is required." : "";
  }
  if (name.length < 2) return "Enter a valid name.";
  if (!/^[a-zA-Z\s.'.-]+$/.test(name)) {
    return "Name can only include letters and basic punctuation.";
  }
  return "";
}

export function validateWebsiteOrProfile(value) {
  const input = value.trim();
  if (!input) return "Website or social profile is required.";

  let candidate = input;
  if (!/^https?:\/\//i.test(candidate)) {
    candidate = `https://${candidate}`;
  }

  let url;
  try {
    url = new URL(candidate);
  } catch {
    return "Enter a valid website or profile URL.";
  }

  if (!["http:", "https:"].includes(url.protocol)) {
    return "URL must start with http:// or https://.";
  }

  if (!url.hostname.includes(".")) {
    return "Enter a complete website or profile link.";
  }

  return "";
}

export function validatePhone(value) {
  const phone = value.trim();
  if (!phone) return "Phone number is required.";

  const compact = phone.replace(/[()\s]/g, "");
  if (!PK_PHONE_PATTERN.test(compact)) {
    return "Enter a valid Pakistan mobile number (e.g. 0300-1234567).";
  }

  return "";
}

export function validateSellerName(value) {
  const name = value.trim();
  if (!name) return "Seller or business name is required.";
  if (name.length < 2) return "Seller name looks too short.";
  if (name.length > 80) return "Seller name is too long.";
  return "";
}

export function normalizeWebsite(value) {
  const input = value.trim();
  if (!input) return "";
  if (/^https?:\/\//i.test(input)) return input;
  return `https://${input}`;
}
