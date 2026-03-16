# PolicyChatbot

Chatbot hỏi đáp policy cho quản lý dự án phần mềm.

Repository: `https://github.com/Zygoo13/PolicyChatbot`

Project gồm 2 phần:

- `backend`: xử lý API, retrieval, gọi Gemini
- `frontend`: giao diện chat cho người dùng

---

## 1. Yêu cầu trước khi chạy

Máy cần cài sẵn:

- Git
- Python 3.10+ 
- Node.js 18+
- npm

Kiểm tra nhanh:

```bash
git --version
python --version
node --version
npm --version
```

---

## 2. Clone project

```bash
git clone https://github.com/Zygoo13/PolicyChatbot.git
cd PolicyChatbot
```

---

## 3. Cấu trúc thư mục

```bash
PolicyChatbot/
├── backend/
├── frontend/
└── README.md
```

---

## 4. Chạy Backend

### Bước 1: vào thư mục backend

```bash
cd backend
```

### Bước 2: tạo môi trường ảo

### Windows (PowerShell)

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
```

### Bước 3: cài thư viện

```bash
pip install -r requirements.txt
```

### Bước 4: tạo file `.env`

Trong thư mục `backend`, tạo file:

```bash
.env
```

Nếu có sẵn file mẫu `.env.example` thì copy:

### Windows

```bash
copy .env.example .env
```

### macOS / Linux

```bash
cp .env.example .env
```

### Bước 5: thay Gemini API Key

Mở file `backend/.env` và sửa giá trị:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Ví dụ:

```env
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxx
```

Lưu ý:

- Mỗi thành viên tự dùng API key của mình
- Không push file `.env` lên GitHub
- Nếu project có thêm biến môi trường khác thì giữ nguyên, chỉ thay `GEMINI_API_KEY`

### Bước 6: chạy backend

```bash
uvicorn app.main:app --reload
```

Backend chạy tại:

```bash
http://127.0.0.1:8000
```

Nếu có docs của FastAPI thì mở:

```bash
http://127.0.0.1:8000/docs
```

---

## 5. Chạy Frontend

Mở terminal mới, quay về thư mục project rồi vào `frontend`:

```bash
cd frontend
```

### Bước 1: cài thư viện

```bash
npm install
```

### Bước 2: chạy frontend

```bash
npm run dev
```

Frontend chạy tại:

```bash
http://localhost:5173/
```

---

## 6. Thứ tự chạy project

Mỗi lần chạy project, làm theo thứ tự này:

### Terminal 1: chạy backend

```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

### Terminal 2: chạy frontend

```bash
cd frontend
npm install
npm run dev
```

Sau đó mở trình duyệt tại:

```bash
http://localhost:5173/
```

---

## 7. File `.env` mẫu

Ví dụ `backend/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Nếu project cần thêm biến khác thì bổ sung bên dưới.

---

## 8. Lỗi thường gặp

### 1. Thiếu thư viện Python

Lỗi kiểu:

```bash
ModuleNotFoundError
```

Cách xử lý:

```bash
pip install -r requirements.txt
```

---

### 2. Chưa activate virtual environment

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

---

### 3. Thiếu hoặc sai `GEMINI_API_KEY`

Kiểm tra file:

```bash
backend/.env
```

Đảm bảo có dòng:

```env
GEMINI_API_KEY=your_real_key
```

---

### 4. Frontend không gọi được backend

Kiểm tra:

- backend đã chạy chưa
- backend có đang ở `http://127.0.0.1:8000` không
- frontend có gọi đúng URL API không

---

### 5. Port bị chiếm

Nếu cổng 8000 đang bị dùng:

```bash
uvicorn app.main:app --reload --port 8001
```

Nếu frontend bị trùng port thì Vite thường tự đổi sang cổng khác.

---

### 6. Cảnh báo Gemini package deprecated

Nếu thấy cảnh báo liên quan `google.generativeai`, đây là cảnh báo package cũ đã deprecated.

Project hiện tại vẫn có thể chạy nếu API hoạt động bình thường. Sau này nhóm có thể nâng cấp code sang package mới nếu cần.

---

## 9. Quy ước làm việc nhóm

- Không push file `.env`
- Nên pull code mới nhất trước khi làm:

```bash
git pull origin main
```

- Nếu cài thêm thư viện:
  - backend: cập nhật `requirements.txt`
  - frontend: cập nhật `package.json`

---

## 10. Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Tạo `backend/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Chạy backend:

```bash
uvicorn app.main:app --reload
```

### Frontend

Mở terminal mới:

```bash
cd frontend
npm install
npm run dev
```

Mở trình duyệt:

```bash
http://localhost:5173/
```
