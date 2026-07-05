/**
 * Centralized environment configuration for the frontend.
 */
export const ENV = {
  // If Vite injects the env var during build (e.g., on Vercel), use it.
  // Otherwise, calculate dynamically based on whether we're on localhost.
  API_BASE_URL: (() => {
    if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) {
      return import.meta.env.VITE_API_URL;
    }
    const isLocal = window.location.origin.includes("127.0.0.1") || 
                    window.location.origin.includes("localhost") || 
                    window.location.origin.includes("4173");
    
    // Default fallback to Render deployment
    return isLocal ? "http://127.0.0.1:5000" : "https://nompyr-backend.onrender.com";
  })()
};
