import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Play, Music, Trash2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { usePlayer } from '../context/PlayerContext'
import { libraryService, catalogService } from '../services/api'

interface Playlist {
  playlist_id: string
  name: string
  is_private: boolean
  track_count: number
  created_at: string
}

interface LibraryTrack {
  track_id: string
  saved_at: string
}

interface Track {
  track_id: string
  title: string
  duration_ms: number
  album?: { album_id: string; title: string; cover_url?: string }
  artists?: Array<{ artist_id: string; name: string }>
}

export default function Library() {
  const { token } = useAuth()
  const { playTrack } = usePlayer()
  const [playlists, setPlaylists] = useState<Playlist[]>([])
  const [libraryTracks, setLibraryTracks] = useState<Track[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newPlaylistName, setNewPlaylistName] = useState('')
  const [activeTab, setActiveTab] = useState<'playlists' | 'tracks'>('playlists')

  useEffect(() => {
    fetchData()
  }, [token])

  const fetchData = async () => {
    if (!token) return
    try {
      const [playlistsData, libraryData] = await Promise.all([
        libraryService.getPlaylists(token),
        libraryService.getLibraryTracks(token)
      ])
      setPlaylists(playlistsData)
      
      const trackDetails = await Promise.all(
        libraryData.map((lt: LibraryTrack) => catalogService.getTrack(token, lt.track_id).catch(() => null))
      )
      setLibraryTracks(trackDetails.filter(Boolean))
    } catch (e) {
      console.error('Failed to fetch library:', e)
    } finally {
      setLoading(false)
    }
  }

  const createPlaylist = async () => {
    if (!token || !newPlaylistName.trim()) return
    try {
      await libraryService.createPlaylist(token, newPlaylistName)
      setNewPlaylistName('')
      setShowCreateModal(false)
      fetchData()
    } catch (e) {
      console.error('Failed to create playlist:', e)
    }
  }

  const deletePlaylist = async (playlistId: string) => {
    if (!token) return
    try {
      await libraryService.deletePlaylist(token, playlistId)
      fetchData()
    } catch (e) {
      console.error('Failed to delete playlist:', e)
    }
  }

  const removeFromLibrary = async (trackId: string) => {
    if (!token) return
    try {
      await libraryService.removeFromLibrary(token, trackId)
      setLibraryTracks(prev => prev.filter(t => t.track_id !== trackId))
    } catch (e) {
      console.error('Failed to remove from library:', e)
    }
  }

  const formatDuration = (ms: number) => {
    const mins = Math.floor(ms / 60000)
    const secs = Math.floor((ms % 60000) / 1000)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Your Library</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-full transition-colors"
        >
          <Plus size={20} />
          New Playlist
        </button>
      </div>

      <div className="flex gap-4 border-b border-dark-400">
        <button
          onClick={() => setActiveTab('playlists')}
          className={`pb-3 px-2 font-medium transition-colors ${
            activeTab === 'playlists' ? 'text-white border-b-2 border-primary-500' : 'text-gray-400 hover:text-white'
          }`}
        >
          Playlists
        </button>
        <button
          onClick={() => setActiveTab('tracks')}
          className={`pb-3 px-2 font-medium transition-colors ${
            activeTab === 'tracks' ? 'text-white border-b-2 border-primary-500' : 'text-gray-400 hover:text-white'
          }`}
        >
          Liked Songs
        </button>
      </div>

      {activeTab === 'playlists' && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {playlists.map((playlist) => (
            <div key={playlist.playlist_id} className="bg-dark-300 rounded-lg p-4 hover:bg-dark-400 transition-colors group relative">
              <Link to={`/playlist/${playlist.playlist_id}`}>
                <div className="aspect-square bg-dark-400 rounded-lg mb-3 flex items-center justify-center">
                  <Music size={48} className="text-gray-500" />
                </div>
                <h3 className="font-semibold text-white truncate">{playlist.name}</h3>
                <p className="text-sm text-gray-400">{playlist.track_count} tracks</p>
              </Link>
              <button
                onClick={(e) => { e.preventDefault(); deletePlaylist(playlist.playlist_id); }}
                className="absolute top-2 right-2 p-2 bg-red-500/80 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Trash2 size={16} className="text-white" />
              </button>
            </div>
          ))}
          {playlists.length === 0 && (
            <div className="col-span-full text-center py-12">
              <p className="text-gray-400">No playlists yet. Create one to get started!</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'tracks' && (
        <div className="space-y-2">
          {libraryTracks.map((track) => (
            <div
              key={track.track_id}
              className="flex items-center gap-4 p-3 bg-dark-300 rounded-lg hover:bg-dark-400 transition-colors group"
            >
              <div
                className="flex-1 flex items-center gap-4 cursor-pointer"
                onClick={() => playTrack(track)}
              >
                <div className="w-12 h-12 bg-dark-400 rounded flex items-center justify-center relative">
                  {track.album?.cover_url ? (
                    <img src={track.album.cover_url} alt="" className="w-full h-full object-cover rounded" />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-primary-600 to-primary-800 rounded" />
                  )}
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded">
                    <Play size={20} className="text-white" />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-white truncate">{track.title}</p>
                  <p className="text-sm text-gray-400 truncate">
                    {track.artists?.map(a => a.name).join(', ') || 'Unknown Artist'}
                  </p>
                </div>
                <span className="text-gray-400 text-sm">{formatDuration(track.duration_ms)}</span>
              </div>
              <button
                onClick={() => removeFromLibrary(track.track_id)}
                className="p-2 text-gray-400 hover:text-red-500 transition-colors"
              >
                <Trash2 size={18} />
              </button>
            </div>
          ))}
          {libraryTracks.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-400">No liked songs yet. Start exploring!</p>
            </div>
          )}
        </div>
      )}

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-dark-200 rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-white mb-4">Create Playlist</h2>
            <input
              type="text"
              value={newPlaylistName}
              onChange={(e) => setNewPlaylistName(e.target.value)}
              placeholder="Playlist name"
              className="w-full px-4 py-3 bg-dark-300 border border-dark-400 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary-500 mb-4"
              autoFocus
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={createPlaylist}
                className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
