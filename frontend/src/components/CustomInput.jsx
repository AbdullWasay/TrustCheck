function CustomInput({
  label,
  type = "text",
  value,
  onChange,
  placeholder = "",
  required = false,
  error = "",
}) {
  return (
    <div className={`input-group${error ? " has-error" : ""}`}>
      <label>
        {label}
        {required && <span className="required"> *</span>}
      </label>

      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        aria-invalid={Boolean(error)}
        className={error ? "input-invalid" : undefined}
      />

      {error && <p className="input-error">{error}</p>}
    </div>
  );
}

export default CustomInput;