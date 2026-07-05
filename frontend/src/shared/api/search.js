import { apiClient } from './base';

export const searchApi = {
  searchAnime: async (query, fallback = false) => {
    // Determine the correct search endpoint based on the query params
    const endpoint = fallback 
      ? `/api/search?keyword=${encodeURIComponent(query)}&fallback=true`
      : `/api/search?keyword=${encodeURIComponent(query)}`;
      
    return await apiClient.get(endpoint);
  }
};
