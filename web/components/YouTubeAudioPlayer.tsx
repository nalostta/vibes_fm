"use client";
import { useEffect, useState } from "react";
import { useNowPlaying } from "@/components/NowPlayingContext";
import { ensureYouTubePlayer, subscribe, getTimes, seekTo } from "@/lib/youtubeManager";

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

function getStartSeconds(input: string): number | null {
  try {
    const u = new URL(input);
    const t = u.searchParams.get("t");
    if (!t) return null;
    // supports seconds (e.g., 1928) or XmYs (e.g., 32m8s)
    if (/^\d+$/.test(t)) return Number(t);
    const m = t.match(/(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?/i);
    if (!m) return null;
    const h = Number(m[1] || 0), min = Number(m[2] || 0), s = Number(m[3] || 0);
    return h * 3600 + min * 60 + s;
  } catch { return null; }
}

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
  const [ready, setReady] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [current, setCurrent] = useState(0);
  const vid = getVideoId(url);
  const { state: np, requestPlayYouTube } = useNowPlaying();
  const isActive = np.current?.type === "youtube" && np.current.id === (vid || "");
  const isGloballyPlaying = isActive && np.playing;

  useEffect(() => {
    let interval: any;
    const tick = () => {
      if (!vid) return;
      const { current: t, duration: d } = getTimes(vid);
      setCurrent(t);
      setDuration(d);
    };
    if (ready) interval = setInterval(tick, 500);
    return () => interval && clearInterval(interval);
  }, [ready]);

  // Ensure a cached player exists for this videoId
  useEffect(() => {
    if (!vid) return;
    let unsubscribe: null | (() => void) = null;
    (async () => {
      await ensureYouTubePlayer(vid);
      setReady(true);
      unsubscribe = subscribe(vid, (evt) => {
        if (evt.type === 'state') {
          const st = evt.data;
          if (st === 1) setPlaying(true);
          else if (st === 2 || st === 0) setPlaying(false);
        } else if (evt.type === 'ready') {
          setReady(true);
        }
      });
    })();
    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, []);

  const toggle = () => {
    if (!vid) return;
    // Delegate to NowPlaying so others get paused
    const startSeconds = getStartSeconds(url) ?? undefined;
    void requestPlayYouTube(vid, { title, startSeconds });
  };

  const seekBy = (delta: number) => {
    if (!vid || !ready) return;
    const { current: cur, duration: dur } = getTimes(vid);
    const next = Math.max(0, Math.min(dur, cur + delta));
    seekTo(vid, next);
    setCurrent(next);
  };

  const onSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!vid || !ready) return;
    const v = Number(e.target.value);
    seekTo(vid, v);
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
            <span aria-hidden>{isGloballyPlaying ? "❚❚" : "►"}</span>
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
      {/* Uses shared offscreen player; no local iframe needed */}
    </div>
  );
}
