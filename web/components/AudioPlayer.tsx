"use client";
import { useRef, useState } from "react";
import { useNowPlaying } from "@/components/NowPlayingContext";

type Props = {
  src?: string | null;
  title?: string;
};

export default function AudioPlayer({ src, title }: Props) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [loading, setLoading] = useState(false);
  const hasSrc = Boolean(src && src.trim().length > 0);
  const { state: np, requestPlayAudio, pauseAll } = useNowPlaying();

  const isActive = np.current?.type === "audio" && np.current.id === (src || title || "");
  const isGloballyPlaying = isActive && np.playing;

  const toggle = () => {
    if (!hasSrc) return;
    const el = audioRef.current;
    if (!el) return;
    if (el.paused) {
      try {
        setLoading(true);
        // Delegate to NowPlaying to pause others and play this element
        void requestPlayAudio(el, { id: src || title || "", title });
        setPlaying(true);
        setLoading(false);
      } catch {
        setPlaying(false);
        setLoading(false);
      }
    } else {
      el.pause();
      pauseAll();
      setPlaying(false);
    }
  };

  const changeSpeed = (v: number) => {
    if (!hasSrc) return;
    const el = audioRef.current;
    if (!el) return;
    el.playbackRate = v;
    setSpeed(v);
  };

  const seekBy = (delta: number) => {
    if (!hasSrc) return;
    const el = audioRef.current;
    if (!el) return;
    const next = Math.max(0, Math.min((el.duration || Infinity), (el.currentTime || 0) + delta));
    el.currentTime = next;
  };

  return (
    <div className="w-full rounded border border-white/10 p-3 bg-black/30">
      <div className="flex items-center justify-end gap-3">
        <div className="flex items-center gap-3">
          <button
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); toggle(); }}
            disabled={!hasSrc || loading}
            aria-label={playing ? "Pause" : "Play"}
            className="px-3 py-2 rounded-md bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed text-base"
            title={playing ? "Pause" : "Play"}
          >
            <span aria-hidden className="text-lg leading-none">{loading ? "…" : (isGloballyPlaying ? "❚❚" : "►")}</span>
          </button>
          <button
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); seekBy(10); }}
            disabled={!hasSrc || loading}
            aria-label="Forward 10 seconds"
            className="px-3 py-2 rounded-md bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed text-base"
            title="Forward 10s"
          >
            <span aria-hidden className="text-sm font-medium">+10s</span>
          </button>
          <label className="text-xs text-white/70">Speed</label>
          <select
            className="bg-transparent border border-white/10 rounded px-2 py-1 text-xs disabled:opacity-50"
            value={speed}
            onChange={(e) => { e.preventDefault(); e.stopPropagation(); changeSpeed(Number(e.target.value)); }}
            disabled={!hasSrc || loading}
          >
            <option value={0.75}>0.75x</option>
            <option value={1}>1x</option>
            <option value={1.25}>1.25x</option>
            <option value={1.5}>1.5x</option>
          </select>
        </div>
      </div>
      {hasSrc ? (
        <audio
          ref={audioRef}
          src={src ?? undefined}
          className="w-full mt-3"
          preload="metadata"
          playsInline
          controls
          onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
        />
      ) : (
        <div className="w-full mt-3 h-10 rounded bg-black/50 border border-white/10 flex items-center justify-center text-xs text-white/70">
          No audio source provided
        </div>
      )}
    </div>
  );
}
