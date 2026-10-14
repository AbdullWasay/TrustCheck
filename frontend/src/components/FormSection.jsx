function FormSection({ title, description, children }) {
  return (
    <section className="form-section">
      <h2>{title}</h2>

      {description && (
        <p className="section-description">{description}</p>
      )}

      <div className="form-section-content">
        {children}
      </div>
    </section>
  );
}

export default FormSection;