import { apiClient } from './base';

export const animeApi = {
  getDetails: async (slug) => {
    return await apiClient.get(`/api/anime/${encodeURIComponent(slug)}`);
  },
  
  // Future methods for episodes/sources can go here
  getEpisodes: async (id) => {
    return await apiClient.get(`/api/anime/${encodeURIComponent(id)}/episodes`);
  },
  
  getSources: async (episodeId) => {
    return await apiClient.get(`/api/anime/sources?id=${encodeURIComponent(episodeId)}`);
  }
};
