import { createContext, useContext, useState, useRef, ReactNode, useEffect } from 'react'
import { streamService, historyService } from '../services/api'
import { useAuth } from './AuthContext'

interface Track {
  track_id: string
  title: string
  duration_ms: number
  album?: {
    album_id: string
    title: string
    cover_url?: string
  }
  artists?: Array<{
    artist_id: string
    name: string
  }>
}

interface PlayerContextType {
  currentTrack: Track | null
  isPlaying: boolean
  progress: number
  duration: number
  volume: number
  queue: Track[]
  playTrack: (track: Track) => void
  togglePlay: () => void
  seekTo: (time: number) => void
  setVolume: (volume: number) => void
  addToQueue: (track: Track) => void
  playNext: () => void
  playPrevious: () => void
}

const PlayerContext = createContext<PlayerContextType | undefined>(undefined)

export function PlayerProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth()
  const [currentTrack, setCurrentTrack] = useState<Track | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolumeState] = useState(0.7)
  const [queue, setQueue] = useState<Track[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const startTimeRef = useRef<number>(0)

  useEffect(() => {
    audioRef.current = new Audio()
    audioRef.current.volume = volume

    audioRef.current.addEventListener('timeupdate', () => {
      if (audioRef.current) {
        setProgress(audioRef.current.currentTime)
      }
    })

    audioRef.current.addEventListener('loadedmetadata', () => {
      if (audioRef.current) {
        setDuration(audioRef.current.duration)
      }
    })

    audioRef.current.addEventListener('ended', () => {
      handleTrackEnd()
    })

    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
    }
  }, [])

  const handleTrackEnd = async () => {
    if (sessionId && token && currentTrack) {
      const playDuration = Math.floor((Date.now() - startTimeRef.current))
      try {
        await streamService.endPlayback(token, sessionId, playDuration)
        await historyService.recordPlayback(token, currentTrack.track_id, playDuration, 'player')
      } catch (e) {
        console.error('Failed to record playback:', e)
      }
    }
    playNext()
  }

  const playTrack = async (track: Track) => {
    if (!token) return

    try {
      const streamData = await streamService.getStreamUrl(token, track.track_id)
      
      if (audioRef.current) {
        audioRef.current.src = streamData.stream_url
        audioRef.current.play()
        setCurrentTrack(track)
        setIsPlaying(true)
        startTimeRef.current = Date.now()

        const session = await streamService.startPlayback(token, track.track_id, 'player')
        setSessionId(session.session_id)
      }
    } catch (e) {
      console.error('Failed to play track:', e)
    }
  }

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause()
      } else {
        audioRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const seekTo = (time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time
      setProgress(time)
    }
  }

  const setVolume = (newVolume: number) => {
    if (audioRef.current) {
      audioRef.current.volume = newVolume
    }
    setVolumeState(newVolume)
  }

  const addToQueue = (track: Track) => {
    setQueue(prev => [...prev, track])
  }

  const playNext = () => {
    if (queue.length > 0) {
      const [nextTrack, ...rest] = queue
      setQueue(rest)
      playTrack(nextTrack)
    } else {
      setIsPlaying(false)
      setCurrentTrack(null)
    }
  }

  const playPrevious = () => {
    if (audioRef.current && progress > 3) {
      audioRef.current.currentTime = 0
      setProgress(0)
    }
  }

  return (
    <PlayerContext.Provider value={{
      currentTrack,
      isPlaying,
      progress,
      duration,
      volume,
      queue,
      playTrack,
      togglePlay,
      seekTo,
      setVolume,
      addToQueue,
      playNext,
      playPrevious
    }}>
      {children}
    </PlayerContext.Provider>
  )
}

export function usePlayer() {
  const context = useContext(PlayerContext)
  if (context === undefined) {
    throw new Error('usePlayer must be used within a PlayerProvider')
  }
  return context
}
