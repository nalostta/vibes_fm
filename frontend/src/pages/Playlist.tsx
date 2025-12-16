import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Play, Clock, Music, Trash2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { usePlayer } from '../context/PlayerContext'
import { libraryService, catalogService } from '../services/api'

interface PlaylistTrack {
  playlist_track_id: number
  track_id: string
  position: number
  added_at: string
}

interface Track {
  track_id: string
  title: string
  duration_ms: number
  album?: { album_id: string; title: string; cover_url?: string }
  artists?: Array<{ artist_id: string; name: string }>
}

interface PlaylistData {
  playlist_id: string
  name: string
  is_private: boolean
  created_at: string
  tracks: PlaylistTrack[]
}

export default function Playlist() {
  const { id } = useParams<{ id: string }>()
  const { token } = useAuth()
  const { playTrack } = usePlayer()
  const [playlist, setPlaylist] = useState<PlaylistData | null>(null)
  const [tracks, setTracks] = useState<Track[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPlaylist()
  }, [id, token])

  const fetchPlaylist = async () => {
    if (!token || !id) return
    try {
      const playlistData = await libraryService.getPlaylist(token, id)
      setPlaylist(playlistData)
      
      const trackDetails = await Promise.all(
        playlistData.tracks.map((pt: PlaylistTrack) => 
          catalogService.getTrack(token, pt.track_id).catch(() => null)
        )
      )
      setTracks(trackDetails.filter(Boolean))
    } catch (e) {
      console.error('Failed to fetch playlist:', e)
    } finally {
      setLoading(false)
    }
  }

  const removeTrack = async (trackId: string) => {
    if (!token || !id) return
    try {
      await libraryService.removeTrackFromPlaylist(token, id, trackId)
      setTracks(prev => prev.filter(t => t.track_id !== trackId))
      if (playlist) {
        setPlaylist({
          ...playlist,
          tracks: playlist.tracks.filter(t => t.track_id !== trackId)
        })
      }
    } catch (e) {
      console.error('Failed to remove track:', e)
    }
  }

  const playAll = () => {
    if (tracks.length > 0) {
      playTrack(tracks[0])
    }
  }

  const formatDuration = (ms: number) => {
    const mins = Math.floor(ms / 60000)
    const secs = Math.floor((ms % 60000) / 1000)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getTotalDuration = () => {
    const totalMs = tracks.reduce((acc, t) => acc + t.duration_ms, 0)
    const hours = Math.floor(totalMs / 3600000)
    const mins = Math.floor((totalMs % 3600000) / 60000)
    if (hours > 0) {
      return `${hours} hr ${mins} min`
    }
    return `${mins} min`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  if (!playlist) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">Playlist not found</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-end gap-6">
        <div className="w-48 h-48 bg-dark-300 rounded-lg flex items-center justify-center shadow-xl">
          <Music size={64} className="text-gray-500" />
        </div>
        <div>
          <p className="text-sm text-gray-400 uppercase">Playlist</p>
          <h1 className="text-5xl font-bold text-white mt-2 mb-4">{playlist.name}</h1>
          <p className="text-gray-400">
            {tracks.length} songs, {getTotalDuration()}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={playAll}
          disabled={tracks.length === 0}
          className="w-14 h-14 bg-primary-500 hover:bg-primary-400 rounded-full flex items-center justify-center transition-colors disabled:opacity-50"
        >
          <Play size={28} className="text-white ml-1" />
        </button>
      </div>

      {tracks.length > 0 ? (
        <div className="bg-dark-300/50 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-400 text-gray-400 text-sm">
                <th className="text-left py-3 px-4 w-12">#</th>
                <th className="text-left py-3 px-4">Title</th>
                <th className="text-left py-3 px-4">Album</th>
                <th className="text-right py-3 px-4 w-20">
                  <Clock size={16} />
                </th>
                <th className="w-12"></th>
              </tr>
            </thead>
            <tbody>
              {tracks.map((track, index) => (
                <tr
                  key={track.track_id}
                  className="hover:bg-dark-400/50 transition-colors group"
                >
                  <td className="py-3 px-4 text-gray-400">
                    <span className="group-hover:hidden">{index + 1}</span>
                    <Play
                      size={16}
                      className="hidden group-hover:block text-white cursor-pointer"
                      onClick={() => playTrack(track)}
                    />
                  </td>
                  <td className="py-3 px-4 cursor-pointer" onClick={() => playTrack(track)}>
                    <p className="font-medium text-white">{track.title}</p>
                    <p className="text-sm text-gray-400">
                      {track.artists?.map(a => a.name).join(', ') || 'Unknown Artist'}
                    </p>
                  </td>
                  <td className="py-3 px-4 text-gray-400">
                    {track.album?.title || 'Single'}
                  </td>
                  <td className="py-3 px-4 text-gray-400 text-right">
                    {formatDuration(track.duration_ms)}
                  </td>
                  <td className="py-3 px-4">
                    <button
                      onClick={() => removeTrack(track.track_id)}
                      className="p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-dark-300/50 rounded-lg">
          <p className="text-gray-400">This playlist is empty. Add some tracks!</p>
        </div>
      )}
    </div>
  )
}
