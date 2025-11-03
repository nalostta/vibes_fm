"use client";
import { useNowPlaying } from "@/components/NowPlayingContext";
import { useEffect, useState } from "react";

export default function NowPlayingBar() {
  const { state, toggle, pauseAll, stop, seekBy, seekTo, next, prev, position, duration } = useNowPlaying();
  const title = state.current?.title ?? (state.current?.type === "audio" ? state.current?.id : state.current ? `YouTube ${state.current.id}` : "");

  // We don't yet expose position/duration directly; poll using available sources
  useEffect(() => {
    let id: any;
    id = setInterval(() => {
      // Lightweight: rely on native audio timeupdate wired in context, but mirror here through queue index changes
      // For robustness, we keep local slider state responsive; context handlers update underlying media
    }, 1000);
    return () => clearInterval(id);
  }, [state.index, state.current?.type]);

  if (!state.current) return null;

  return (
    <div className="sticky bottom-4 z-40 w-full border-t border-white/10 bg-black/80 backdrop-blur supports-[backdrop-filter]:bg-black/60 rounded-md shadow-md mx-auto max-w-6xl">
      <div className="px-4 py-3 flex flex-col gap-3">
        <div className="flex items-center justify-between gap-3">
          <div className="truncate text-base text-white/85">Now playing: {title}</div>
          <div className="flex items-center gap-3">
            <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); prev(); }} className="px-3 py-2 rounded-md bg-white/10 hover:bg-white/20 text-base" aria-label="Previous" title="Previous">⏮</button>
            <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); seekBy(-10); }} className="px-3 py-2 rounded-md bg-white/10 hover:bg-white/20 text-base" aria-label="Rewind 10s" title="Rewind 10s">−10s</button>
            <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); toggle(); }} className="px-3 py-2 rounded-md bg-white/10 hover:bg-white/20 text-base" aria-label={state.playing ? "Pause" : "Play"} title={state.playing ? "Pause" : "Play"}>{state.playing ? "❚❚" : "►"}</button>
            <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); seekBy(10); }} className="px-3 py-2 rounded-md bg-white/10 hover:bg-white/20 text-base" aria-label="Forward 10s" title="Forward 10s">+10s</button>
            <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); next(); }} className="px-3 py-2 rounded-md bg-white/10 hover:bg-white/20 text-base" aria-label="Next" title="Next">⏭</button>
            <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); stop(); }} className="px-3 py-2 rounded-md bg-white/10 hover:bg-white/20 text-base" aria-label="Stop" title="Stop">■</button>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <input
            type="range"
            className="w-full"
            min={0}
            max={Math.max(1, Math.floor(duration || 0))}
            step={1}
            value={Math.floor(position || 0)}
            onChange={(e) => { e.preventDefault(); e.stopPropagation(); seekTo(Number(e.target.value)); }}
          />
          <div className="text-sm text-white/70 w-28 text-right">{fmt(position)} / {fmt(duration)}</div>
        </div>
      </div>
    </div>
  );
}

function fmt(s: number) {
  const m = Math.floor((s || 0) / 60);
  const sec = Math.floor((s || 0) % 60).toString().padStart(2, "0");
  return `${m}:${sec}`;
}
