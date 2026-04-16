// Base template load script trong <head>, nên DOM chưa có nút -> không thể bind trực tiếp.
// Dùng event delegation để nút `.update-cart` ở mọi trang đều hoạt động.

var ADD_CART_SUCCESS_MS = 1800;

function formatCartCurrency(n) {
    var num = Math.round(Number(n) || 0);
    return num.toLocaleString('vi-VN') + 'đ';
}

/** Đồng bộ trang Giỏ hàng (số lượng, thành tiền dòng, tóm tắt) sau POST /update_item/ — không reload nếu còn sản phẩm. */
function applyCartPageUpdate(data) {
    var root = document.querySelector('.cart-page');
    if (!root || typeof data.cartTotal === 'undefined') return false;

    if (typeof data.productId !== 'undefined') {
        var row = root.querySelector('.cart-item[data-product-id="' + data.productId + '"]');
        if (row) {
            if (data.lineRemoved) {
                row.remove();
            } else {
                var input = row.querySelector('.qty-input');
                if (input && typeof data.lineQuantity !== 'undefined') {
                    input.value = String(data.lineQuantity);
                }
                if (typeof data.lineTotal !== 'undefined') {
                    row.querySelectorAll('.js-cart-line-total').forEach(function (el) {
                        el.textContent = formatCartCurrency(data.lineTotal);
                    });
                }
                row.querySelectorAll('.update-cart[data-action="delete"]').forEach(function (btn) {
                    if (typeof data.lineQuantity !== 'undefined') {
                        btn.setAttribute('data-quantity', String(data.lineQuantity));
                    }
                });
            }
        }
    }

    if (typeof data.cartItems !== 'undefined') {
        root.querySelectorAll('.js-cart-page-total-items').forEach(function (el) {
            el.textContent = String(data.cartItems);
        });
    }
    root.querySelectorAll('.js-cart-page-subtotal').forEach(function (el) {
        el.textContent = formatCartCurrency(data.cartTotal);
    });
    root.querySelectorAll('.js-cart-page-grand-total').forEach(function (el) {
        el.textContent = formatCartCurrency(data.cartTotal);
    });

    if (data.cartItems === 0) {
        window.location.reload();
        return true;
    }
    return false;
}

function showAddToCartSuccess() {
    var el = document.getElementById('add-cart-success-overlay');
    if (!el) return;
    clearTimeout(el._hideTimer);
    clearTimeout(el._afterHideTimer);
    el.classList.add('is-open');
    el.setAttribute('aria-hidden', 'false');
    el._hideTimer = setTimeout(function () {
        el.classList.remove('is-open');
        el.setAttribute('aria-hidden', 'true');
        el._afterHideTimer = setTimeout(function () {}, 320);
    }, ADD_CART_SUCCESS_MS);
}

document.addEventListener('click', function (e) {
    const btn = e.target && e.target.closest ? e.target.closest('.update-cart') : null
    if (!btn) return

    const productId = btn.dataset.product
    const action = btn.dataset.action

    console.log('productId', productId, 'action', action)
    console.log('user: ', user)

    if (!productId || !action) return

    if (user === "AnonymousUser"){
        // Chưa đăng nhập: chuyển sang trang login và quay lại đúng trang sau khi login
        const nextUrl = window.location.pathname + window.location.search
        window.location.href = '/login/?next=' + encodeURIComponent(nextUrl)
        return
    }

    if (action === 'delete'){
        const qty = parseInt(btn.dataset.quantity || '1', 10) || 1
        deleteCartItem(productId, qty)
    } else {
        var suppressSuccessToast = btn.getAttribute('data-qty-adjust') === '1'
        updateUserOrder(productId, action, suppressSuccessToast)
    }
})

function updateUserOrder(productId, action, suppressSuccessToast){
    console.log('user logged in')
    var url = '/update_item/'
    fetch(url, {
        method: 'POST',
        headers:{
            'Content-Type':'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({'productId':productId, 'action':action})
    })
    .then(function (response) {
        return response.json().then(function (data) {
            return { response: response, data: data }
        }).catch(function () {
            return { response: response, data: {} }
        })
    })
    .then(function (result) {
        var response = result.response
        var data = result.data || {}
        console.log('data', data)
        if (!response.ok || data.ok === false) {
            return
        }
        var badge = document.getElementById('cart-total')
        if (badge && typeof data.cartItems !== 'undefined') {
            badge.textContent = data.cartItems
        }
        if (applyCartPageUpdate(data)) {
            return;
        }
        if (action === 'add' && !suppressSuccessToast) {
            showAddToCartSuccess()
        }
    })
    .catch(function () {})
}

function deleteCartItem(productId, quantity){
    // Không đổi backend: xóa = gọi 'remove' nhiều lần tới khi item bị delete
    let remaining = Math.max(1, quantity)
    const url = '/update_item/'

    const step = () => {
        fetch(url, {
            method: 'POST',
            headers:{
                'Content-Type':'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({'productId':productId, 'action':'remove'})
        })
        .then((response) => response.json())
        .then(() => {
            remaining -= 1
            if (remaining > 0){
                step()
            } else {
                setTimeout(() => {
                    location.reload()
                }, 150)
            }
        })
        .catch(() => {
            // fallback reload nếu có lỗi mạng
            location.reload()
        })
    }

    step()
}
