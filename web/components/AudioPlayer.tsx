"use client";
import { useRef, useState } from "react";

type Props = {
  src?: string | null;
  title?: string;
};

export default function AudioPlayer({ src, title }: Props) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const hasSrc = Boolean(src && src.trim().length > 0);

  const toggle = () => {
    if (!hasSrc) return;
    const el = audioRef.current;
    if (!el) return;
    if (el.paused) {
      el.play();
      setPlaying(true);
    } else {
      el.pause();
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

  return (
    <div className="w-full rounded border border-white/10 p-3 bg-black/30">
      <div className="flex items-center justify-between gap-4">
        <div className="truncate text-sm">
          <span className="text-white/80">{title ?? "Untitled Mix"}</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={toggle} disabled={!hasSrc} className="px-3 py-1 rounded bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed text-sm">
            {playing ? "Pause" : "Play"}
          </button>
          <label className="text-xs text-white/70">Speed</label>
          <select
            className="bg-transparent border border-white/10 rounded px-2 py-1 text-xs disabled:opacity-50"
            value={speed}
            onChange={(e) => changeSpeed(Number(e.target.value))}
            disabled={!hasSrc}
          >
            <option value={0.75}>0.75x</option>
            <option value={1}>1x</option>
            <option value={1.25}>1.25x</option>
            <option value={1.5}>1.5x</option>
          </select>
        </div>
      </div>
      {hasSrc ? (
        <audio ref={audioRef} src={src ?? undefined} className="w-full mt-3" preload="none" controls />
      ) : (
        <div className="w-full mt-3 h-10 rounded bg-black/50 border border-white/10 flex items-center justify-center text-xs text-white/70">
          No audio source provided
        </div>
      )}
    </div>
  );
}
