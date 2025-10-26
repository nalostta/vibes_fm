"use client";
import { useEffect, useRef, useState, useId } from "react";

declare global {
  interface Window {
    YT?: any;
    onYouTubeIframeAPIReady?: () => void;
  }
}

type Props = {
  url: string;
  title?: string;
};

function getVideoId(input: string): string | null {
  try {
    const u = new URL(input);
    if (u.hostname.includes("youtu.be")) return u.pathname.replace(/^\//, "");
    const v = u.searchParams.get("v");
    if (v) return v;
    const m1 = u.pathname.match(/\/embed\/([a-zA-Z0-9_-]{6,})/);
    if (m1) return m1[1];
    const m2 = u.pathname.match(/\/shorts\/([a-zA-Z0-9_-]{6,})/);
    if (m2) return m2[1];
  } catch {}
  return null;
}

export default function YouTubeAudioPlayer({ url, title }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const reactId = useId();
  const playerElIdRef = useRef<string>(`ytp-${reactId}`);
  const playerRef = useRef<any>(null);
  const [ready, setReady] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [current, setCurrent] = useState(0);
  const [queuedPlay, setQueuedPlay] = useState(false);
  const vid = getVideoId(url);

  useEffect(() => {
    let interval: any;
    const tick = () => {
      const p = playerRef.current;
      if (!p) return;
      const t = p.getCurrentTime?.() || 0;
      const d = p.getDuration?.() || 0;
      setCurrent(t);
      setDuration(d);
    };
    if (ready) interval = setInterval(tick, 500);
    return () => interval && clearInterval(interval);
  }, [ready]);

  // Create the player lazily when needed
  useEffect(() => {
    return () => {
      try {
        playerRef.current?.destroy?.();
      } catch {}
      playerRef.current = null;
    };
  }, []);

  const ensurePlayer = async () => {
    if (playerRef.current || !vid) return;
    await new Promise<void>((resolve) => {
      if (window.YT && window.YT.Player) return resolve();
      const scriptId = "yt-iframe-api";
      if (!document.getElementById(scriptId)) {
        const s = document.createElement("script");
        s.id = scriptId;
        s.src = "https://www.youtube.com/iframe_api";
        document.body.appendChild(s);
      }
      const onReadyApi = () => resolve();
      if (window.YT && window.YT.Player) onReadyApi();
      else window.onYouTubeIframeAPIReady = onReadyApi;
    });
    playerRef.current = new window.YT.Player(playerElIdRef.current, {
      height: "0",
      width: "0",
      videoId: vid,
      host: "https://www.youtube.com",
      playerVars: {
        playsinline: 1,
        modestbranding: 1,
        rel: 0,
        enablejsapi: 1,
        origin: typeof window !== "undefined" ? window.location.origin : undefined,
      },
      events: {
        onReady: () => {
          setReady(true);
          if (queuedPlay) {
            try {
              if (typeof playerRef.current?.playVideo === 'function') playerRef.current.playVideo();
              setPlaying(true);
            } catch {}
            setQueuedPlay(false);
          }
        },
        onStateChange: (e: any) => {
          const st = e.data;
          if (st === 1) setPlaying(true);
          else if (st === 2 || st === 0) setPlaying(false);
        },
      },
    });
  };

  const toggle = () => {
    const p = playerRef.current;
    if (!p || !ready) {
      // Queue a play and ensure API/player creation proceeds
      setQueuedPlay(true);
      void ensurePlayer();
      return;
    }
    if (playing) {
      if (typeof p.pauseVideo === 'function') p.pauseVideo();
    } else {
      if (typeof p.playVideo === 'function') p.playVideo();
    }
  };

  const seekBy = (delta: number) => {
    const p = playerRef.current;
    if (!p || !ready) return;
    const getDur = typeof p.getDuration === 'function' ? p.getDuration() : 0;
    const getCur = typeof p.getCurrentTime === 'function' ? p.getCurrentTime() : 0;
    const next = Math.max(0, Math.min(getDur, getCur + delta));
    if (typeof p.seekTo === 'function') p.seekTo(next, true);
    setCurrent(next);
  };

  const onSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const p = playerRef.current;
    if (!p || !ready) return;
    const v = Number(e.target.value);
    if (typeof p.seekTo === 'function') p.seekTo(v, true);
    setCurrent(v);
  };

  const fmt = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60).toString().padStart(2, "0");
    return `${m}:${sec}`;
  };

  return (
    <div className="w-full rounded border border-white/10 p-3 bg-black/30">
      <div className="flex items-center justify-between gap-4">
        <div className="truncate text-sm">
          <span className="text-white/80">{title ?? "YouTube"}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); toggle(); }}
            aria-label={playing ? "Pause" : "Play"}
            className="px-2 py-1 rounded bg-white/10 hover:bg-white/20 disabled:opacity-50 text-sm"
            title={playing ? "Pause" : "Play"}
          >
            <span aria-hidden>{playing ? "❚❚" : "►"}</span>
          </button>
          <button
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); seekBy(10); }}
            disabled={!ready}
            aria-label="Forward 10 seconds"
            className="px-2 py-1 rounded bg-white/10 hover:bg-white/20 disabled:opacity-50 text-sm"
            title="Forward 10s"
          >
            <span aria-hidden>+10s</span>
          </button>
          <span className="text-xs text-white/60">
            {fmt(current)} / {fmt(duration)}
          </span>
        </div>
      </div>
      <input
        className="w-full mt-3"
        type="range"
        min={0}
        max={Math.max(1, Math.floor(duration))}
        step={1}
        value={Math.floor(current)}
        onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
        onChange={(e) => { e.preventDefault(); e.stopPropagation(); onSeek(e); }}
      />
      <div style={{ width: 0, height: 0, overflow: "hidden" }}>
        <div id={playerElIdRef.current} ref={containerRef} />
      </div>
    </div>
  );
}
