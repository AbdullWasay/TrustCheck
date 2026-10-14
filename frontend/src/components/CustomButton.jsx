function CustomButton({
  children,
  onClick,
  type = "button",
  disabled = false,
}) {
  return (
    <button
      className="custom-button"
      type={type}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

export default CustomButton;