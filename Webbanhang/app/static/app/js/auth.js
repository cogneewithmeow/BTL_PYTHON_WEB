(() => {
  function setIcon(btn, isVisible) {
    const icon = btn.querySelector("i");
    if (!icon) return;
    icon.classList.toggle("fa-eye", !isVisible);
    icon.classList.toggle("fa-eye-slash", isVisible);
  }

  function togglePassword(btn) {
    const targetSel = btn.getAttribute("data-auth-target");
    if (!targetSel) return;
    const input = document.querySelector(targetSel);
    if (!input) return;

    const isPassword = input.getAttribute("type") === "password";
    input.setAttribute("type", isPassword ? "text" : "password");
    setIcon(btn, isPassword);
    input.focus({ preventScroll: true });
  }

  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-auth-toggle='password']");
    if (!btn) return;
    e.preventDefault();
    togglePassword(btn);
  });

  document.querySelectorAll("[data-auth-toggle='password']").forEach((btn) => {
    setIcon(btn, false);
  });
})();

