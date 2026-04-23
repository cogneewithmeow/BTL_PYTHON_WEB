# 🛍️ Web Bán Hàng Django

Một ứng dụng web bán hàng được xây dựng bằng **Django**, cho phép người dùng duyệt sản phẩm, thêm vào giỏ hàng, và thanh toán trực tuyến.

## 📋 Tính Năng Chính

- ✅ **Quản lý Sản Phẩm** - Hiển thị danh sách sản phẩm với hình ảnh và giá
- ✅ **Giỏ Hàng Động** - Thêm/xóa sản phẩm, cập nhật số lượng (AJAX)
- ✅ **Hệ thống Khách Hàng** - Đăng ký, đăng nhập, lưu thông tin cá nhân
- ✅ **Quản lý Đơn Hàng** - Tạo, tracking đơn hàng
- ✅ **Địa Chỉ Giao Hàng** - Lưu và quản lý địa chỉ giao hàng
- ✅ **Thanh Toán** - Hỗ trợ giao dịch trực tuyến (transaction_id)
- ✅ **Sản Phẩm Số Hóa** - Hỗ trợ sản phẩm kỹ thuật số
- ✅ **Tìm Kiếm & Danh Mục** - Tìm kiếm sản phẩm, lọc theo danh mục
- ✅ **Profile Người Dùng** - Cập nhật thông tin cá nhân, avatar
- ✅ **Chatbot AI** - Hỏi đáp trực tiếp ngay trên website (floating button + chat panel)

## 🏗️ Cấu Trúc Dự Án

```
Webbanhang/
├── app/                          # Ứng dụng chính
│   ├── models.py                # Models: Category, Product, Order, OrderItem, ShippingAddress, Profile
│   ├── views.py                 # Views: home, cart, checkout, login, register, profile, etc.
│   ├── urls.py                  # URL routing: home, register, login, cart, checkout, etc.
│   ├── admin.py                 # Admin Django
│   ├── static/
│   │   ├── css/main.css         # Stylesheet chính
│   │   ├── js/main.js           # JavaScript chính
│   │   └── image/               # Hình ảnh sản phẩm và banner
│   └── templates/
│       └── app/
│           ├── base.html        # Template cơ sở
│           ├── home.html        # Trang chủ
│           ├── cart.html        # Giỏ hàng
│           ├── checkout.html    # Thanh toán
│           ├── login.html       # Đăng nhập
│           ├── register.html    # Đăng ký
│           ├── profile.html     # Profile
│           └── success.html     # Thành công
├── Webbanhang/                  # Cấu hình Django chính
│   ├── settings.py              # Cấu hình ứng dụng
│   ├── urls.py                  # URL routing chính
│   └── wsgi.py                  # WSGI config
├── manage.py                    # Django management
└── db.sqlite3                   # Database
```

## 📊 Mô Hình Dữ Liệu

### 1. **Category** - Danh Mục
```python
- sub_category: ForeignKey (danh mục con)
- is_sub: BooleanField (là danh mục con?)
- name: CharField
- slug: SlugField (unique)
```

### 2. **Product** - Sản Phẩm
```python
- category: ManyToManyField (Category)
- name: CharField
- price: IntegerField
- digital: BooleanField (sản phẩm số hóa?)
- image: ImageField
- detail: TextField
- ImageUrl: Property (URL hình ảnh)
```

### 3. **Order** - Đơn Hàng
```python
- customer: ForeignKey (User)
- date_order: DateTimeField (ngày tạo)
- complete: BooleanField (hoàn thành?)
- transaction_id: CharField (ID giao dịch)
- get_cart_items: Property (tổng số lượng)
- get_cart_total: Property (tổng tiền)
```

### 4. **OrderItem** - Chi Tiết Đơn Hàng
```python
- product: ForeignKey (Product)
- order: ForeignKey (Order)
- quantity: IntegerField (số lượng)
- date_added: DateTimeField (ngày thêm)
- get_total: Method (tổng tiền item)
```

### 5. **ShippingAddress** - Địa Chỉ Giao Hàng
```python
- customer: ForeignKey (User)
- order: ForeignKey (Order)
- address: CharField (địa chỉ)
- city: CharField (thành phố)
- state: CharField (tỉnh/bang)
- mobile: CharField (số điện thoại)
- date_added: DateTimeField (ngày thêm)
```

### 6. **Profile** - Hồ Sơ Người Dùng
```python
- user: OneToOneField (User)
- phone: CharField
- address: CharField
- avatar: ImageField (upload_to='avatars/')
- Signal: Tự động tạo Profile khi tạo User
```

### 7. **CreateUserForm** - Form Đăng Ký Tùy Chỉnh
```python
- Thừa kế UserCreationForm
- Thêm field: phone
- Fields: username, email, first_name, last_name, password1, password2
```

## 🚀 Cài Đặt & Chạy

### 1. Clone dự án
```bash
cd d:\Python_WEB\Webbanhang
```

### 2. Cài đặt dependencies
```bash
pip install django pillow
```

### 3. Thực hiện migration
```bash
python manage.py migrate
```

### 4. Tạo superuser (admin)
```bash
python manage.py createsuperuser
```

### 5. Chạy server
```bash
python manage.py runserver
```

Server sẽ chạy tại: `http://127.0.0.1:8000/`

## 📄 Các Trang Chính & URL

- **Trang Chủ** (`/` - home) - Hiển thị danh sách sản phẩm
- **Đăng Ký** (`/register/` - register) - Tạo tài khoản mới
- **Đăng Nhập** (`/login/` - login) - Đăng nhập tài khoản
- **Đăng Xuất** (`/logout/` - logout) - Đăng xuất
- **Tìm Kiếm** (`/search/` - search) - Tìm kiếm sản phẩm
- **Danh Mục** (`/category/` - category) - Lọc sản phẩm theo danh mục
- **Giỏ Hàng** (`/cart/` - cart) - Xem, sửa giỏ hàng
- **Chi Tiết Sản Phẩm** (`/detail/` - detail) - Xem chi tiết sản phẩm
- **Profile** (`/profile/` - profile) - Xem và cập nhật thông tin cá nhân
- **Thanh Toán** (`/checkout/` - checkout) - Nhập địa chỉ, thực hiện thanh toán
- **Thành Công** (`/success/` - success) - Trang xác nhận thanh toán
- **Cập Nhật Giỏ Hàng** (`/update_item/` - updateItem) - AJAX cập nhật số lượng
- **Cập Nhật Profile** (`/update_profile/` - update_profile) - Cập nhật thông tin cá nhân
- **API Chatbot AI** (`/api/chat/` - api_chat) - Nhận `message/history` và trả `reply`

## 🤖 Cấu hình Chatbot AI (OpenRouter)

Chatbot được thiết kế để **chỉ backend** dùng API key (tách riêng trong `app/ai/chat_service.py`) và gọi AI qua **OpenRouter**:

- Base URL: `https://openrouter.ai/api/v1`
- Endpoint: `POST /api/chat/`

### Biến môi trường

- **`OPENAI_API_KEY`**: bắt buộc để chatbot hoạt động thật (key OpenRouter)
- **`OPENAI_MODEL`**: tùy chọn, mặc định `openai/gpt-4o-mini`

File mẫu: `.env.example`

### Ví dụ (Windows PowerShell)

```powershell
$env:OPENAI_API_KEY="YOUR_KEY"
$env:OPENAI_MODEL="openai/gpt-4o-mini"
python manage.py runserver
```

## 🔧 Công Nghệ Sử Dụng

- **Backend**: Django 3.x+
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript (AJAX cho giỏ hàng)
- **Image**: Pillow

## 📝 Yêu Cầu Hệ Thống

- Python 3.8+
- pip (Python package manager)
- Django
- Pillow (xử lý hình ảnh)

## 👨‍💻 Hướng Dẫn Đóng Góp

1. Fork dự án
2. Tạo branch mới (`git checkout -b feature/TinhNangMoi`)
3. Commit thay đổi (`git commit -m 'Thêm tính năng mới'`)
4. Push lên branch (`git push origin feature/TinhNangMoi`)
5. Tạo Pull Request

## 📞 Liên Hệ

Nếu có vấn đề, vui lòng tạo issue trong repository.

---
**Phát triển bởi**: Python Web Developer  
**Ngày cập nhật**: April 13, 2026