const product = document.querySelector("#product-type");
const material = document.querySelector("#material");

function setVisible(selector, visible) {
  document.querySelectorAll(selector).forEach((element) => {
    element.hidden = !visible;
  });
}

function updateFields() {
  const value = product.value;
  const isCard = value === "business_cards";
  const isDigital = value === "flyers" || value === "brochures";
  const isBanner = value === "banners";
  setVisible(".print-field", isCard || isDigital);
  setVisible(".digital-field", isDigital);
  setVisible(".brochure-field", value === "brochures");
  setVisible(".banner-field", isBanner);

  for (const option of material.options) {
    const allowed = isCard
      ? ["smooth", "designer"].includes(option.value)
      : isDigital
        ? ["90", "120", "160"].includes(option.value)
        : ["banner_440", "poster_150", "vinyl"].includes(option.value);
    option.hidden = !allowed;
    option.disabled = !allowed;
  }
  if (material.selectedOptions[0]?.disabled) {
    material.value = isCard ? "smooth" : isDigital ? "160" : "banner_440";
  }
}

product.addEventListener("change", updateFields);
updateFields();
