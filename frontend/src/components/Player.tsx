import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX } from 'lucide-react'
import { usePlayer } from '../context/PlayerContext'

export default function Player() {
  const {
    currentTrack,
    isPlaying,
    progress,
    duration,
    volume,
    togglePlay,
    seekTo,
    setVolume,
    playNext,
    playPrevious
  } = usePlayer()

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (!currentTrack) {
    return (
      <div className="h-20 bg-dark-200 border-t border-dark-300 flex items-center justify-center">
        <p className="text-gray-500">No track playing</p>
      </div>
    )
  }

  return (
    <div className="h-20 bg-dark-200 border-t border-dark-300 px-4 flex items-center justify-between">
      <div className="flex items-center gap-4 w-1/4">
        <div className="w-14 h-14 bg-dark-400 rounded flex items-center justify-center">
          {currentTrack.album?.cover_url ? (
            <img
              src={currentTrack.album.cover_url}
              alt={currentTrack.album.title}
              className="w-full h-full object-cover rounded"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-primary-600 to-primary-800 rounded" />
          )}
        </div>
        <div>
          <p className="text-sm font-medium text-white truncate max-w-[180px]">
            {currentTrack.title}
          </p>
          <p className="text-xs text-gray-400 truncate max-w-[180px]">
            {currentTrack.artists?.map(a => a.name).join(', ') || 'Unknown Artist'}
          </p>
        </div>
      </div>

      <div className="flex flex-col items-center gap-2 w-2/4">
        <div className="flex items-center gap-4">
          <button
            onClick={playPrevious}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <SkipBack size={20} />
          </button>
          <button
            onClick={togglePlay}
            className="w-10 h-10 bg-white rounded-full flex items-center justify-center hover:scale-105 transition-transform"
          >
            {isPlaying ? (
              <Pause size={20} className="text-black" />
            ) : (
              <Play size={20} className="text-black ml-1" />
            )}
          </button>
          <button
            onClick={playNext}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <SkipForward size={20} />
          </button>
        </div>

        <div className="flex items-center gap-2 w-full max-w-md">
          <span className="text-xs text-gray-400 w-10 text-right">
            {formatTime(progress)}
          </span>
          <input
            type="range"
            min={0}
            max={duration || 100}
            value={progress}
            onChange={(e) => seekTo(Number(e.target.value))}
            className="flex-1 h-1 bg-dark-400 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:rounded-full"
          />
          <span className="text-xs text-gray-400 w-10">
            {formatTime(duration)}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 w-1/4 justify-end">
        <button
          onClick={() => setVolume(volume === 0 ? 0.7 : 0)}
          className="text-gray-400 hover:text-white transition-colors"
        >
          {volume === 0 ? <VolumeX size={20} /> : <Volume2 size={20} />}
        </button>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={volume}
          onChange={(e) => setVolume(Number(e.target.value))}
          className="w-24 h-1 bg-dark-400 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:rounded-full"
        />
      </div>
    </div>
  )
}
