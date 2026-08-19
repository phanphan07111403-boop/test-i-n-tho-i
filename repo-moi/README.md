# repo-moi

Repository mới — dự án khởi tạo với TypeScript và Node.js.

## Yêu cầu

- Node.js 20 trở lên

## Cài đặt

```bash
npm install
```

## Chạy development

```bash
npm run dev
```

## Build & chạy production

```bash
npm run build
npm start
```

Server mặc định chạy tại `http://localhost:3000`.

## Tạo repository trên GitHub

Từ thư mục gốc của monorepo, chạy:

```bash
./scripts/create-github-repo.sh
```

Hoặc tạo thủ công trên [GitHub](https://github.com/new) với tên `repo-moi`, sau đó:

```bash
cd repo-moi
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/phanphan07111403-boop/repo-moi.git
git push -u origin main
```
