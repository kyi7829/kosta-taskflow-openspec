/**
 * config.js — Environment configuration
 *
 * For local development with FastAPI running on port 8000,
 * include this script BEFORE api.js and uncomment the line below:
 */

// Detect if running locally (not deployed to Vercel)
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
  // When serving frontend with live-server on port 5500, API calls go through
  // You may need to set this if FastAPI is on a different port:
  // window.API_BASE_URL = 'http://localhost:8000';
  // If FastAPI is proxied at /api via reverse proxy, leave this commented out.
}
