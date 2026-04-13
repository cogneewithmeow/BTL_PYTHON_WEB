# 🛍️ Web Bán Hàng Django

Một ứng dụng web bán hàng được xây dựng bằng **Django**, cho phép người dùng duyệt sản phẩm, thêm vào giỏ hàng, và thanh toán trực tuyến.

## 📋 Tính Năng Chính

- ✅ **Quản lý Sản Phẩm** - Hiển thị danh sách sản phẩm với hình ảnh và giá
- ✅ **Giỏ Hàng Động** - Thêm/xóa sản phẩm, cập nhật số lượng
- ✅ **Hệ thống Khách Hàng** - Đăng ký, đăng nhập, lưu thông tin cá nhân
- ✅ **Quản lý Đơn Hàng** - Tạo, tracking đơn hàng
- ✅ **Địa Chỉ Giao Hàng** - Lưu và quản lý địa chỉ giao hàng
- ✅ **Thanh Toán** - Hỗ trợ giao dịch trực tuyến (transaction_id)
- ✅ **Sản Phẩm Số Hóa** - Hỗ trợ sản phẩm kỹ thuật số

## 🏗️ Cấu Trúc Dự Án

```
Webbanhang/
├── app/                          # Ứng dụng chính
│   ├── models.py                # Models: Customer, Product, Order, OrderItem, ShippingAddress
│   ├── views.py                 # Views xử lý logic
│   ├── urls.py                  # URL routing
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
│           └── checkout.html    # Thanh toán
├── Webbanhang/                  # Cấu hình Django chính
│   ├── settings.py              # Cấu hình ứng dụng
│   ├── urls.py                  # URL routing chính
│   └── wsgi.py                  # WSGI config
├── manage.py                    # Django management
└── db.sqlite3                   # Database
```

## 📊 Mô Hình Dữ Liệu

### 1. **Customer** - Khách Hàng
```python
- user: OneToOneField (Django User)
- name: CharField
- email: CharField
```

### 2. **Product** - Sản Phẩm
```python
- name: CharField
- price: IntegerField
- digital: BooleanField (sản phẩm số hóa?)
- image: ImageField
```

### 3. **Order** - Đơn Hàng
```python
- customer: ForeignKey (Khách Hàng)
- date_order: DateTimeField (ngày tạo)
- complete: BooleanField (hoàn thành?)
- transaction_id: CharField (ID giao dịch)
```

### 4. **OrderItem** - Chi Tiết Đơn Hàng
```python
- product: ForeignKey (Sản Phẩm)
- order: ForeignKey (Đơn Hàng)
- quantity: IntegerField (số lượng)
- date_added: DateTimeField (ngày thêm)
```

### 5. **ShippingAddress** - Địa Chỉ Giao Hàng
```python
- customer: ForeignKey (Khách Hàng)
- order: ForeignKey (Đơn Hàng)
- address: CharField (địa chỉ)
- city: CharField (thành phố)
- state: CharField (tỉnh/bang)
- mobile: CharField (số điện thoại)
- date_added: DateTimeField (ngày thêm)
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

## 📄 Các Trang Chính

- **Trang Chủ** (`home.html`) - Hiển thị danh sách sản phẩm
- **Giỏ Hàng** (`cart.html`) - Xem, sửa giỏ hàng
- **Thanh Toán** (`checkout.html`) - Nhập địa chỉ, thực hiện thanh toán

## 🔧 Công Nghệ Sử Dụng

- **Backend**: Django 3.x+
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
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
**Ngày cập nhật**: April 3, 2026