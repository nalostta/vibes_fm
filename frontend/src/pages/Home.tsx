import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Play, Clock } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { usePlayer } from '../context/PlayerContext'
import { catalogService, historyService } from '../services/api'

interface Track {
  track_id: string
  title: string
  duration_ms: number
  album?: { album_id: string; title: string; cover_url?: string }
  artists?: Array<{ artist_id: string; name: string }>
}

interface Album {
  album_id: string
  title: string
  cover_url?: string
  artist?: { artist_id: string; name: string }
}

interface Stats {
  total_plays: number
  total_duration_ms: number
  unique_tracks: number
  top_tracks: Array<{ track_id: string; play_count: number }>
}

export default function Home() {
  const { token } = useAuth()
  const { playTrack } = usePlayer()
  const [recentTracks, setRecentTracks] = useState<Track[]>([])
  const [albums, setAlbums] = useState<Album[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      if (!token) return
      try {
        const [tracksData, albumsData, statsData] = await Promise.all([
          catalogService.getTracks(token, { limit: 10 }),
          catalogService.getAlbums(token, { limit: 6 }),
          historyService.getStats(token, 7)
        ])
        setRecentTracks(tracksData)
        setAlbums(albumsData)
        setStats(statsData)
      } catch (e) {
        console.error('Failed to fetch data:', e)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [token])

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
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold text-white mb-6">Good evening</h1>
        
        {stats && (
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="bg-dark-300 rounded-lg p-4">
              <p className="text-gray-400 text-sm">Plays this week</p>
              <p className="text-2xl font-bold text-white">{stats.total_plays}</p>
            </div>
            <div className="bg-dark-300 rounded-lg p-4">
              <p className="text-gray-400 text-sm">Minutes listened</p>
              <p className="text-2xl font-bold text-white">{Math.floor(stats.total_duration_ms / 60000)}</p>
            </div>
            <div className="bg-dark-300 rounded-lg p-4">
              <p className="text-gray-400 text-sm">Unique tracks</p>
              <p className="text-2xl font-bold text-white">{stats.unique_tracks}</p>
            </div>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-2xl font-bold text-white mb-4">Browse Albums</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {albums.map((album) => (
            <Link
              key={album.album_id}
              to={`/album/${album.album_id}`}
              className="bg-dark-300 rounded-lg p-4 hover:bg-dark-400 transition-colors group"
            >
              <div className="aspect-square bg-dark-400 rounded-lg mb-4 overflow-hidden relative">
                {album.cover_url ? (
                  <img src={album.cover_url} alt={album.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-primary-600 to-primary-800" />
                )}
                <button className="absolute bottom-2 right-2 w-12 h-12 bg-primary-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-lg">
                  <Play size={24} className="text-white ml-1" />
                </button>
              </div>
              <h3 className="font-semibold text-white truncate">{album.title}</h3>
              <p className="text-sm text-gray-400 truncate">{album.artist?.name || 'Unknown Artist'}</p>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold text-white mb-4">Tracks</h2>
        <div className="bg-dark-300 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-400 text-gray-400 text-sm">
                <th className="text-left py-3 px-4 w-12">#</th>
                <th className="text-left py-3 px-4">Title</th>
                <th className="text-left py-3 px-4">Album</th>
                <th className="text-right py-3 px-4 w-20">
                  <Clock size={16} />
                </th>
              </tr>
            </thead>
            <tbody>
              {recentTracks.map((track, index) => (
                <tr
                  key={track.track_id}
                  className="hover:bg-dark-400 transition-colors cursor-pointer group"
                  onClick={() => playTrack(track)}
                >
                  <td className="py-3 px-4 text-gray-400">
                    <span className="group-hover:hidden">{index + 1}</span>
                    <Play size={16} className="hidden group-hover:block text-white" />
                  </td>
                  <td className="py-3 px-4">
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
