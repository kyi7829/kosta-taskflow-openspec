// 로컬 개발: API가 8000, 프론트가 5500이므로 절대 URL 사용
// 운영(Vercel): 같은 도메인의 /api 경로 사용
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
  window.API_BASE_URL = 'http://localhost:8000';
}
