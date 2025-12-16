import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Play } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { usePlayer } from '../context/PlayerContext'
import { catalogService } from '../services/api'

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
  release_date?: string
}

interface ArtistData {
  artist_id: string
  name: string
  bio?: string
  image_url?: string
}

export default function Artist() {
  const { id } = useParams<{ id: string }>()
  const { token } = useAuth()
  const { playTrack } = usePlayer()
  const [artist, setArtist] = useState<ArtistData | null>(null)
  const [albums, setAlbums] = useState<Album[]>([])
  const [topTracks, setTopTracks] = useState<Track[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchArtist()
  }, [id, token])

  const fetchArtist = async () => {
    if (!token || !id) return
    try {
      const [artistData, albumsData, tracksData] = await Promise.all([
        catalogService.getArtist(token, id),
        catalogService.getAlbums(token, { artist_id: id }),
        catalogService.getTracks(token, { limit: 5 })
      ])
      setArtist(artistData)
      setAlbums(albumsData)
      setTopTracks(tracksData.filter((t: Track) => t.artists?.some(a => a.artist_id === id)))
    } catch (e) {
      console.error('Failed to fetch artist:', e)
    } finally {
      setLoading(false)
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

  if (!artist) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">Artist not found</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-end gap-6">
        <div className="w-48 h-48 bg-dark-300 rounded-full shadow-xl overflow-hidden">
          {artist.image_url ? (
            <img src={artist.image_url} alt={artist.name} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-primary-600 to-primary-800" />
          )}
        </div>
        <div>
          <p className="text-sm text-gray-400 uppercase">Artist</p>
          <h1 className="text-5xl font-bold text-white mt-2 mb-4">{artist.name}</h1>
          {artist.bio && (
            <p className="text-gray-400 max-w-2xl">{artist.bio}</p>
          )}
        </div>
      </div>

      {topTracks.length > 0 && (
        <section>
          <h2 className="text-2xl font-bold text-white mb-4">Popular</h2>
          <div className="space-y-2">
            {topTracks.map((track, index) => (
              <div
                key={track.track_id}
                className="flex items-center gap-4 p-3 rounded-lg hover:bg-dark-300 transition-colors cursor-pointer group"
                onClick={() => playTrack(track)}
              >
                <span className="w-6 text-gray-400 text-center group-hover:hidden">{index + 1}</span>
                <Play size={16} className="w-6 text-white hidden group-hover:block" />
                <div className="w-12 h-12 bg-dark-400 rounded overflow-hidden">
                  {track.album?.cover_url ? (
                    <img src={track.album.cover_url} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-primary-600 to-primary-800" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-white truncate">{track.title}</p>
                </div>
                <span className="text-gray-400 text-sm">{formatDuration(track.duration_ms)}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {albums.length > 0 && (
        <section>
          <h2 className="text-2xl font-bold text-white mb-4">Albums</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {albums.map((album) => (
              <Link
                key={album.album_id}
                to={`/album/${album.album_id}`}
                className="bg-dark-300 rounded-lg p-4 hover:bg-dark-400 transition-colors group"
              >
                <div className="aspect-square bg-dark-400 rounded-lg mb-3 overflow-hidden relative">
                  {album.cover_url ? (
                    <img src={album.cover_url} alt={album.title} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-primary-600 to-primary-800" />
                  )}
                  <button className="absolute bottom-2 right-2 w-10 h-10 bg-primary-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-lg">
                    <Play size={20} className="text-white ml-0.5" />
                  </button>
                </div>
                <h3 className="font-semibold text-white truncate">{album.title}</h3>
                {album.release_date && (
                  <p className="text-sm text-gray-400">{new Date(album.release_date).getFullYear()}</p>
                )}
              </Link>
            ))}
          </div>
        </section>
      )}

      {albums.length === 0 && topTracks.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-400">No content available for this artist</p>
        </div>
      )}
    </div>
  )
}
