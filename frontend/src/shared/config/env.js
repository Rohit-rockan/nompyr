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
    // Universally use relative paths to leverage Vite/Vercel proxies
    return "";
  })()
};
