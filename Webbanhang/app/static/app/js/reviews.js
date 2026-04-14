function initStarPicker() {
  const forms = Array.from(document.querySelectorAll('form.review-form'));
  if (!forms.length) return;

  forms.forEach((form) => {
    const picker = form.querySelector('.star-picker');
    const input = form.querySelector('input[name="rating"]');
    if (!picker || !input) return;

    const initial = parseInt(picker.getAttribute('data-initial') || '0', 10) || 0;
    const buttons = Array.from(picker.querySelectorAll('.star-btn'));

    function render(value) {
      buttons.forEach((btn) => {
        const v = parseInt(btn.getAttribute('data-value'), 10);
        btn.classList.toggle('active', v <= value);
      });
    }

    render(initial);
    if (initial) input.value = String(initial);

    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const v = parseInt(btn.getAttribute('data-value'), 10);
        input.value = String(v);
        render(v);
      });
    });
  });
}

function initImagePreview() {
  const forms = Array.from(document.querySelectorAll('form.review-form'));
  if (!forms.length) return;

  forms.forEach((form) => {
    const input = form.querySelector('input[type="file"][name="images"]');
    const preview = form.querySelector('.review-preview');
    if (!input || !preview) return;

    input.addEventListener('change', () => {
      const all = Array.from(input.files || []);
      if (all.length > 6) {
        // chặn vượt quá 6 ảnh
        input.value = '';
        preview.innerHTML = '';
        return;
      }

      preview.innerHTML = '';
      all.slice(0, 6).forEach((file) => {
        const url = URL.createObjectURL(file);
        const img = document.createElement('img');
        img.src = url;
        img.onload = () => URL.revokeObjectURL(url);
        preview.appendChild(img);
      });
    });
  });
}

function initHelpfulButtons() {
  const buttons = Array.from(document.querySelectorAll('.helpful-btn'));
  if (!buttons.length) return;

  buttons.forEach((btn) => {
    btn.addEventListener('click', async () => {
      const url = btn.getAttribute('data-url');
      if (!url) return;

      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: {
            'X-CSRFToken': (typeof csrftoken !== 'undefined' ? csrftoken : ''),
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({}),
        });
        const data = await res.json();
        if (!data.ok) return;
        const countEl = btn.querySelector('.helpful-count');
        if (countEl) countEl.textContent = String(data.helpful_count);
        btn.classList.toggle('btn-secondary', data.liked);
        btn.classList.toggle('btn-outline-secondary', !data.liked);
      } catch (e) {
        // im lặng để không phá UX nếu fetch fail
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initStarPicker();
  initImagePreview();
  initHelpfulButtons();
});

