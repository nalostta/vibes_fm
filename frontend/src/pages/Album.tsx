import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Play, Clock, Heart } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { usePlayer } from '../context/PlayerContext'
import { catalogService, libraryService } from '../services/api'

interface Track {
  track_id: string
  title: string
  duration_ms: number
  track_number?: number
  artists?: Array<{ artist_id: string; name: string }>
}

interface AlbumData {
  album_id: string
  title: string
  cover_url?: string
  release_date?: string
  artist?: { artist_id: string; name: string }
  tracks: Track[]
}

export default function Album() {
  const { id } = useParams<{ id: string }>()
  const { token } = useAuth()
  const { playTrack } = usePlayer()
  const [album, setAlbum] = useState<AlbumData | null>(null)
  const [loading, setLoading] = useState(true)
  const [likedTracks, setLikedTracks] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetchAlbum()
    fetchLikedTracks()
  }, [id, token])

  const fetchAlbum = async () => {
    if (!token || !id) return
    try {
      const data = await catalogService.getAlbum(token, id)
      setAlbum(data)
    } catch (e) {
      console.error('Failed to fetch album:', e)
    } finally {
      setLoading(false)
    }
  }

  const fetchLikedTracks = async () => {
    if (!token) return
    try {
      const library = await libraryService.getLibraryTracks(token)
      setLikedTracks(new Set(library.map((t: { track_id: string }) => t.track_id)))
    } catch (e) {
      console.error('Failed to fetch library:', e)
    }
  }

  const toggleLike = async (trackId: string) => {
    if (!token) return
    try {
      if (likedTracks.has(trackId)) {
        await libraryService.removeFromLibrary(token, trackId)
        setLikedTracks(prev => {
          const next = new Set(prev)
          next.delete(trackId)
          return next
        })
      } else {
        await libraryService.addToLibrary(token, trackId)
        setLikedTracks(prev => new Set(prev).add(trackId))
      }
    } catch (e) {
      console.error('Failed to toggle like:', e)
    }
  }

  const playAll = () => {
    if (album && album.tracks.length > 0) {
      const trackWithAlbum = {
        ...album.tracks[0],
        album: { album_id: album.album_id, title: album.title, cover_url: album.cover_url }
      }
      playTrack(trackWithAlbum)
    }
  }

  const formatDuration = (ms: number) => {
    const mins = Math.floor(ms / 60000)
    const secs = Math.floor((ms % 60000) / 1000)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getTotalDuration = () => {
    if (!album) return ''
    const totalMs = album.tracks.reduce((acc, t) => acc + t.duration_ms, 0)
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

  if (!album) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">Album not found</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-end gap-6">
        <div className="w-48 h-48 bg-dark-300 rounded-lg shadow-xl overflow-hidden">
          {album.cover_url ? (
            <img src={album.cover_url} alt={album.title} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-primary-600 to-primary-800" />
          )}
        </div>
        <div>
          <p className="text-sm text-gray-400 uppercase">Album</p>
          <h1 className="text-5xl font-bold text-white mt-2 mb-4">{album.title}</h1>
          <div className="flex items-center gap-2 text-gray-400">
            {album.artist && (
              <Link to={`/artist/${album.artist.artist_id}`} className="text-white hover:underline">
                {album.artist.name}
              </Link>
            )}
            {album.release_date && (
              <>
                <span>•</span>
                <span>{new Date(album.release_date).getFullYear()}</span>
              </>
            )}
            <span>•</span>
            <span>{album.tracks.length} songs, {getTotalDuration()}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={playAll}
          disabled={album.tracks.length === 0}
          className="w-14 h-14 bg-primary-500 hover:bg-primary-400 rounded-full flex items-center justify-center transition-colors disabled:opacity-50"
        >
          <Play size={28} className="text-white ml-1" />
        </button>
      </div>

      {album.tracks.length > 0 ? (
        <div className="bg-dark-300/50 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-400 text-gray-400 text-sm">
                <th className="text-left py-3 px-4 w-12">#</th>
                <th className="text-left py-3 px-4">Title</th>
                <th className="w-12"></th>
                <th className="text-right py-3 px-4 w-20">
                  <Clock size={16} />
                </th>
              </tr>
            </thead>
            <tbody>
              {album.tracks.map((track, index) => {
                const trackWithAlbum = {
                  ...track,
                  album: { album_id: album.album_id, title: album.title, cover_url: album.cover_url }
                }
                return (
                  <tr
                    key={track.track_id}
                    className="hover:bg-dark-400/50 transition-colors group"
                  >
                    <td className="py-3 px-4 text-gray-400">
                      <span className="group-hover:hidden">{track.track_number || index + 1}</span>
                      <Play
                        size={16}
                        className="hidden group-hover:block text-white cursor-pointer"
                        onClick={() => playTrack(trackWithAlbum)}
                      />
                    </td>
                    <td className="py-3 px-4 cursor-pointer" onClick={() => playTrack(trackWithAlbum)}>
                      <p className="font-medium text-white">{track.title}</p>
                      <p className="text-sm text-gray-400">
                        {track.artists?.map(a => a.name).join(', ') || album.artist?.name || 'Unknown Artist'}
                      </p>
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => toggleLike(track.track_id)}
                        className={`p-1 transition-colors ${
                          likedTracks.has(track.track_id) ? 'text-primary-500' : 'text-gray-400 hover:text-white opacity-0 group-hover:opacity-100'
                        }`}
                      >
                        <Heart size={16} fill={likedTracks.has(track.track_id) ? 'currentColor' : 'none'} />
                      </button>
                    </td>
                    <td className="py-3 px-4 text-gray-400 text-right">
                      {formatDuration(track.duration_ms)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-dark-300/50 rounded-lg">
          <p className="text-gray-400">No tracks in this album</p>
        </div>
      )}
    </div>
  )
}
