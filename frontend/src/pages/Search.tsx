import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Search as SearchIcon, Play } from 'lucide-react'
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
  artist?: { artist_id: string; name: string }
}

interface Artist {
  artist_id: string
  name: string
  image_url?: string
}

interface SearchResults {
  tracks: Track[]
  albums: Album[]
  artists: Artist[]
}

export default function Search() {
  const { token } = useAuth()
  const { playTrack } = usePlayer()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResults | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || !token) return

    setLoading(true)
    try {
      const data = await catalogService.search(token, query)
      setResults(data)
    } catch (e) {
      console.error('Search failed:', e)
    } finally {
      setLoading(false)
    }
  }

  const formatDuration = (ms: number) => {
    const mins = Math.floor(ms / 60000)
    const secs = Math.floor((ms % 60000) / 1000)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="space-y-8">
      <form onSubmit={handleSearch} className="relative max-w-xl">
        <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="What do you want to listen to?"
          className="w-full pl-12 pr-4 py-3 bg-dark-300 border border-dark-400 rounded-full text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
        />
      </form>

      {loading && (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
        </div>
      )}

      {results && !loading && (
        <div className="space-y-8">
          {results.tracks.length > 0 && (
            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Tracks</h2>
              <div className="space-y-2">
                {results.tracks.slice(0, 5).map((track) => (
                  <div
                    key={track.track_id}
                    className="flex items-center gap-4 p-3 bg-dark-300 rounded-lg hover:bg-dark-400 transition-colors cursor-pointer group"
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
                ))}
              </div>
            </section>
          )}

          {results.albums.length > 0 && (
            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Albums</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {results.albums.slice(0, 6).map((album) => (
                  <Link
                    key={album.album_id}
                    to={`/album/${album.album_id}`}
                    className="bg-dark-300 rounded-lg p-4 hover:bg-dark-400 transition-colors"
                  >
                    <div className="aspect-square bg-dark-400 rounded-lg mb-3 overflow-hidden">
                      {album.cover_url ? (
                        <img src={album.cover_url} alt={album.title} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full bg-gradient-to-br from-primary-600 to-primary-800" />
                      )}
                    </div>
                    <h3 className="font-semibold text-white truncate">{album.title}</h3>
                    <p className="text-sm text-gray-400 truncate">{album.artist?.name || 'Unknown Artist'}</p>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {results.artists.length > 0 && (
            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Artists</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {results.artists.slice(0, 6).map((artist) => (
                  <Link
                    key={artist.artist_id}
                    to={`/artist/${artist.artist_id}`}
                    className="bg-dark-300 rounded-lg p-4 hover:bg-dark-400 transition-colors text-center"
                  >
                    <div className="aspect-square bg-dark-400 rounded-full mb-3 mx-auto overflow-hidden">
                      {artist.image_url ? (
                        <img src={artist.image_url} alt={artist.name} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full bg-gradient-to-br from-primary-600 to-primary-800" />
                      )}
                    </div>
                    <h3 className="font-semibold text-white truncate">{artist.name}</h3>
                    <p className="text-sm text-gray-400">Artist</p>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {results.tracks.length === 0 && results.albums.length === 0 && results.artists.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-400">No results found for "{query}"</p>
            </div>
          )}
        </div>
      )}

      {!results && !loading && (
        <div className="text-center py-12">
          <p className="text-gray-400">Search for tracks, albums, or artists</p>
        </div>
      )}
    </div>
  )
}
