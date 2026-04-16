// Product detail page: quantity + multi-add without breaking existing cart.js
(function () {
  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function getCsrfToken() {
    if (typeof csrftoken !== 'undefined' && csrftoken) return csrftoken;
    const el = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return el ? el.value : '';
  }

  function isAnonymous() {
    return typeof user !== 'undefined' && user === 'AnonymousUser';
  }

  function toInt(v, fallback) {
    const n = parseInt(String(v || ''), 10);
    return Number.isFinite(n) ? n : fallback;
  }

  async function postUpdate(productId, action) {
    const url = '/update_item/';
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify({ productId, action }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      throw new Error('Cart update failed');
    }
    return data;
  }

  async function addMany(productId, qty) {
    const safeQty = Math.max(1, Math.min(99, toInt(qty, 1)));
    let last = null;
    for (let i = 0; i < safeQty; i++) {
      // backend hiện tại mỗi lần add tăng +1
      // eslint-disable-next-line no-await-in-loop
      last = await postUpdate(productId, 'add');
    }
    return last;
  }

  function initQtyControls(scope) {
    const root = scope || document;
    const wrap = root.querySelector('.pd-qty');
    if (!wrap) return;
    const input = wrap.querySelector('input.pd-qty__input');
    const btnMinus = wrap.querySelector('[data-qty="minus"]');
    const btnPlus = wrap.querySelector('[data-qty="plus"]');
    const min = toInt(input && input.getAttribute('min'), 1) || 1;
    const max = toInt(input && input.getAttribute('max'), 99) || 99;

    function clamp(n) {
      return Math.max(min, Math.min(max, n));
    }

    function setVal(n) {
      if (!input) return;
      input.value = String(clamp(n));
    }

    function getVal() {
      if (!input) return 1;
      return clamp(toInt(input.value, 1));
    }

    if (btnMinus) {
      btnMinus.addEventListener('click', () => setVal(getVal() - 1));
    }
    if (btnPlus) {
      btnPlus.addEventListener('click', () => setVal(getVal() + 1));
    }
    if (input) {
      input.addEventListener('change', () => setVal(getVal()));
      input.addEventListener('input', () => {
        // chỉ cho số
        input.value = input.value.replace(/[^\d]/g, '');
      });
    }
  }

  function initDetailActions() {
    document.addEventListener('click', async (e) => {
      const btn = e.target && e.target.closest ? e.target.closest('[data-pd-action]') : null;
      if (!btn) return;
      e.preventDefault();

      const productId = btn.getAttribute('data-product');
      const action = btn.getAttribute('data-pd-action'); // add | buy
      const qtyInput = $('.pd-qty__input');
      const qty = qtyInput ? qtyInput.value : '1';

      if (!productId) return;

      if (isAnonymous()) {
        const nextUrl = window.location.pathname + window.location.search;
        window.location.href = '/login/?next=' + encodeURIComponent(nextUrl);
        return;
      }

      btn.setAttribute('aria-busy', 'true');
      btn.classList.add('is-loading');
      try {
        const result = await addMany(productId, qty);
        if (action === 'buy') {
          window.location.href = '/cart/';
        } else {
          const badge = document.getElementById('cart-total');
          if (badge && result && typeof result.cartItems !== 'undefined') {
            badge.textContent = result.cartItems;
          }
          if (typeof showAddToCartSuccess === 'function') {
            showAddToCartSuccess();
          }
        }
      } catch (err) {
        window.location.reload();
      } finally {
        btn.removeAttribute('aria-busy');
        btn.classList.remove('is-loading');
      }
    });
  }

  function initThumbGallery() {
    const main = document.getElementById('pd-mainimg');
    const thumbs = Array.from(document.querySelectorAll('.pd-thumb[data-thumb]'));
    if (!main || !thumbs.length) return;

    thumbs.forEach((btn) => {
      btn.addEventListener('click', () => {
        const url = btn.getAttribute('data-thumb');
        if (!url) return;
        main.src = url;
        thumbs.forEach((b) => b.classList.remove('is-active'));
        btn.classList.add('is-active');
      });
    });
  }

  function initShareLike() {
    document.addEventListener('click', async (e) => {
      const shareBtn = e.target && e.target.closest ? e.target.closest('[data-share]') : null;
      if (shareBtn) {
        const type = shareBtn.getAttribute('data-share');
        const url = window.location.href;

        if (type === 'copy') {
          try {
            if (navigator.clipboard) await navigator.clipboard.writeText(url);
          } catch (_) {
            // ignore
          }
          return;
        }
        if (type === 'fb') {
          window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(url), '_blank', 'noopener,noreferrer');
          return;
        }
        if (type === 'mess') {
          window.open('https://www.facebook.com/dialog/send?link=' + encodeURIComponent(url), '_blank', 'noopener,noreferrer');
        }
        return;
      }

      const likeBtn = e.target && e.target.closest ? e.target.closest('[data-like="toggle"]') : null;
      if (!likeBtn) return;
      const pressed = likeBtn.getAttribute('aria-pressed') === 'true';
      likeBtn.setAttribute('aria-pressed', pressed ? 'false' : 'true');
      likeBtn.classList.toggle('is-active', !pressed);
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initQtyControls();
    initDetailActions();
    initThumbGallery();
    initShareLike();
  });
})();

