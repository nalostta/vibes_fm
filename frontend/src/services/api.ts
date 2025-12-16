import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || ''

const authApi = axios.create({ baseURL: `${API_BASE}/api/auth` })
const userApi = axios.create({ baseURL: `${API_BASE}/api/users` })
const catalogApi = axios.create({ baseURL: `${API_BASE}/api/catalog` })
const streamApi = axios.create({ baseURL: `${API_BASE}/api/stream` })
const libraryApi = axios.create({ baseURL: `${API_BASE}/api/library` })
const historyApi = axios.create({ baseURL: `${API_BASE}/api/history` })

const getAuthHeader = (token: string) => ({ Authorization: `Bearer ${token}` })

export const authService = {
  async login(email: string, password: string) {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    const response = await authApi.post('/login', formData)
    return response.data
  },

  async register(email: string, username: string, password: string) {
    const response = await authApi.post('/register', { email, username, password })
    return response.data
  },

  async getProfile(token: string) {
    const response = await userApi.get('/me', { headers: getAuthHeader(token) })
    return response.data
  }
}

export const catalogService = {
  async getTracks(token: string, params?: { skip?: number; limit?: number; album_id?: string }) {
    const response = await catalogApi.get('/tracks', { headers: getAuthHeader(token), params })
    return response.data
  },

  async getTrack(token: string, trackId: string) {
    const response = await catalogApi.get(`/tracks/${trackId}`, { headers: getAuthHeader(token) })
    return response.data
  },

  async getAlbums(token: string, params?: { skip?: number; limit?: number; artist_id?: string }) {
    const response = await catalogApi.get('/albums', { headers: getAuthHeader(token), params })
    return response.data
  },

  async getAlbum(token: string, albumId: string) {
    const response = await catalogApi.get(`/albums/${albumId}`, { headers: getAuthHeader(token) })
    return response.data
  },

  async getArtists(token: string, params?: { skip?: number; limit?: number }) {
    const response = await catalogApi.get('/artists', { headers: getAuthHeader(token), params })
    return response.data
  },

  async getArtist(token: string, artistId: string) {
    const response = await catalogApi.get(`/artists/${artistId}`, { headers: getAuthHeader(token) })
    return response.data
  },

  async search(token: string, query: string) {
    const response = await catalogApi.get('/search', { headers: getAuthHeader(token), params: { q: query } })
    return response.data
  }
}

export const streamService = {
  async getStreamUrl(token: string, trackId: string, quality: string = 'high') {
    const response = await streamApi.post('/stream', { track_id: trackId, quality }, { headers: getAuthHeader(token) })
    return response.data
  },

  async startPlayback(token: string, trackId: string, source: string = 'player') {
    const response = await streamApi.post('/playback/start', { track_id: trackId, source }, { headers: getAuthHeader(token) })
    return response.data
  },

  async endPlayback(token: string, sessionId: string, playDurationMs: number) {
    const response = await streamApi.post('/playback/end', { session_id: sessionId, play_duration_ms: playDurationMs }, { headers: getAuthHeader(token) })
    return response.data
  }
}

export const libraryService = {
  async getPlaylists(token: string) {
    const response = await libraryApi.get('/playlists', { headers: getAuthHeader(token) })
    return response.data
  },

  async getPlaylist(token: string, playlistId: string) {
    const response = await libraryApi.get(`/playlists/${playlistId}`, { headers: getAuthHeader(token) })
    return response.data
  },

  async createPlaylist(token: string, name: string, isPrivate: boolean = true) {
    const response = await libraryApi.post('/playlists', { name, is_private: isPrivate }, { headers: getAuthHeader(token) })
    return response.data
  },

  async addTrackToPlaylist(token: string, playlistId: string, trackId: string) {
    const response = await libraryApi.post(`/playlists/${playlistId}/tracks`, { track_id: trackId }, { headers: getAuthHeader(token) })
    return response.data
  },

  async removeTrackFromPlaylist(token: string, playlistId: string, trackId: string) {
    await libraryApi.delete(`/playlists/${playlistId}/tracks/${trackId}`, { headers: getAuthHeader(token) })
  },

  async deletePlaylist(token: string, playlistId: string) {
    await libraryApi.delete(`/playlists/${playlistId}`, { headers: getAuthHeader(token) })
  },

  async getLibraryTracks(token: string) {
    const response = await libraryApi.get('/library/tracks', { headers: getAuthHeader(token) })
    return response.data
  },

  async addToLibrary(token: string, trackId: string) {
    const response = await libraryApi.post('/library/tracks', { track_id: trackId }, { headers: getAuthHeader(token) })
    return response.data
  },

  async removeFromLibrary(token: string, trackId: string) {
    await libraryApi.delete(`/library/tracks/${trackId}`, { headers: getAuthHeader(token) })
  }
}

export const historyService = {
  async getHistory(token: string, params?: { skip?: number; limit?: number }) {
    const response = await historyApi.get('/history', { headers: getAuthHeader(token), params })
    return response.data
  },

  async getStats(token: string, days: number = 30) {
    const response = await historyApi.get('/history/stats', { headers: getAuthHeader(token), params: { days } })
    return response.data
  },

  async recordPlayback(token: string, trackId: string, playDurationMs: number, source: string) {
    const response = await historyApi.post('/history', { track_id: trackId, play_duration_ms: playDurationMs, source }, { headers: getAuthHeader(token) })
    return response.data
  }
}
