import { apiClient } from './base';

export const homeApi = {
  getHomeFeed: async () => {
    return await apiClient.get('/api/home');
  }
};
