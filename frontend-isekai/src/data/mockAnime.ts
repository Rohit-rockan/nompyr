export interface AnimeData {
  id: string;
  title: string;
  imageUrl: string;
  genre: string;
}

export const mockAnime: AnimeData[] = [
  { id: '1', title: 'Made in Abyss', imageUrl: 'https://cdn.myanimelist.net/images/anime/6/86733l.jpg', genre: 'Adventure' },
  { id: '2', title: 'Children of the Sea', imageUrl: 'https://cdn.myanimelist.net/images/anime/1167/100494l.jpg', genre: 'Fantasy' },
  { id: '3', title: 'Violet Evergarden', imageUrl: 'https://cdn.myanimelist.net/images/anime/1795/95088l.jpg', genre: 'Drama' },
  { id: '4', title: 'Weathering With You', imageUrl: 'https://cdn.myanimelist.net/images/anime/1880/101118l.jpg', genre: 'Romance' },
  { id: '5', title: 'Spirited Away', imageUrl: 'https://cdn.myanimelist.net/images/anime/6/79597l.jpg', genre: 'Supernatural' },
  { id: '6', title: 'Nagi no Asukara', imageUrl: 'https://cdn.myanimelist.net/images/anime/10/52831l.jpg', genre: 'Drama' },
];
