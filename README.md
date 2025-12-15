# HealthManager (Django + PostgreSQL)

## Yêu cầu
- Python 3.10+
- PostgreSQL 13+
- (Tùy chọn) tạo virtualenv

## Tạo DB PostgreSQL
```sql
CREATE DATABASE healthdb;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE healthdb TO postgres;
```

## Cài đặt
```bash
cd lockun-main
python -m venv .venv
# Windows:
. .venv/Scripts/activate
python -m pip install --upgrade pip

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Truy cập: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Chức năng chính
- Đăng ký/Đăng nhập, hồ sơ sức khỏe (BMI, BMR, TDEE).
- Theo dõi tập luyện (workout): CRUD + tìm kiếm.
- Quản lý dinh dưỡng (meal): CRUD + tìm kiếm.
- Mục tiêu (goal) + tiến độ.
- Thống kê, biểu đồ (Chart.js CDN), xuất CSV/PDF.
- Admin xem danh sách người dùng.
- Chatbox gợi ý (API placeholder / OpenAI) tại `/api/chat/` + widget ở góc dưới.

## Gửi email nhắc nhở
- Cấu hình SMTP trong `.env`.
- Ví dụ gửi test: `python manage.py sendtestmail you@example.com`

## Ghi chú
- KHÔNG dùng sqlite. Cấu hình DB ở `healthmanager/settings.py` đọc từ `.env`.
