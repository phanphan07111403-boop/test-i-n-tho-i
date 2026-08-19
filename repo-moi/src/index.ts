import { createServer } from "node:http";

const PORT = Number(process.env.PORT) || 3000;

createServer((_req, res) => {
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ message: "Xin chào từ repo-moi!", status: "ok" }));
}).listen(PORT, () => {
  console.log(`Server đang chạy tại http://localhost:${PORT}`);
});
