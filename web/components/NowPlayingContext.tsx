"use client";
import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import { ensureYouTubePlayer, pause as ytPause, play as ytPlay, getTimes as ytGetTimes, seekTo as ytSeekTo } from "@/lib/youtubeManager";

export type NowPlayingKind =
  | { type: "audio"; id: string; title?: string; el: HTMLAudioElement | null }
  | { type: "youtube"; id: string; title?: string };

export type NowPlayingState = {
  current: NowPlayingKind | null;
  playing: boolean;
  queue: NowPlayingKind[];
  index: number; // index within queue for current
};

type Ctx = {
  state: NowPlayingState;
  requestPlayAudio: (el: HTMLAudioElement, meta: { id: string; title?: string }) => Promise<void>;
  requestPlayYouTube: (videoId: string, meta: { title?: string; startSeconds?: number }) => Promise<void>;
  toggle: () => void;
  pauseAll: () => void;
  stop: () => void;
  seekBy: (delta: number) => void;
  seekTo: (seconds: number) => void;
  next: () => void;
  prev: () => void;
  position: number;
  duration: number;
};

const NowPlayingContext = createContext<Ctx | null>(null);

export function NowPlayingProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<NowPlayingState>({ current: null, playing: false, queue: [], index: -1 });
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [position, setPosition] = useState(0);
  const [duration, setDuration] = useState(0);

  const pauseAll = () => {
    const cur = state.current;
    if (!cur) return;
    if (cur.type === "audio") {
      cur.el?.pause?.();
    } else if (cur.type === "youtube") {
      ytPause(cur.id);
    }
    setState((s) => ({ ...s, playing: false }));
  };

  const requestPlayAudio = async (el: HTMLAudioElement, meta: { id: string; title?: string }) => {
    pauseAll();
    audioRef.current = el;
    // wire time updates
    el.onloadedmetadata = () => setDuration(el.duration || 0);
    el.ontimeupdate = () => setPosition(el.currentTime || 0);
    try {
      el.load();
      const p = el.play();
      if (p && typeof (p as any).then === "function") await p;
      setState({ current: { type: "audio", id: meta.id, title: meta.title, el }, playing: true, queue: [{ type: "audio", id: meta.id, title: meta.title, el }], index: 0 });
    } catch {
      setState({ current: { type: "audio", id: meta.id, title: meta.title, el }, playing: false, queue: [{ type: "audio", id: meta.id, title: meta.title, el }], index: 0 });
    }
  };

  const requestPlayYouTube = async (videoId: string, meta: { title?: string; startSeconds?: number }) => {
    pauseAll();
    await ensureYouTubePlayer(videoId);
    if (typeof meta.startSeconds === 'number') {
      ytSeekTo(videoId, meta.startSeconds);
    }
    ytPlay(videoId);
    setState({ current: { type: "youtube", id: videoId, title: meta.title }, playing: true, queue: [{ type: "youtube", id: videoId, title: meta.title }], index: 0 });
  };

  const toggle = () => {
    const cur = state.current;
    if (!cur) return;
    if (cur.type === "audio") {
      if (audioRef.current?.paused) audioRef.current?.play?.();
      else audioRef.current?.pause?.();
      setState((s) => ({ ...s, playing: !s.playing }));
    } else if (cur.type === "youtube") {
      if (state.playing) ytPause(cur.id);
      else ytPlay(cur.id);
      setState((s) => ({ ...s, playing: !s.playing }));
    }
  };

  const stop = () => {
    pauseAll();
    setState((s) => ({ ...s, current: s.current, playing: false }));
  };

  const seekBy = (delta: number) => {
    const cur = state.current;
    if (!cur) return;
    if (cur.type === "audio") {
      const el = audioRef.current;
      if (!el) return;
      const next = Math.max(0, Math.min((el.duration || 0), (el.currentTime || 0) + delta));
      el.currentTime = next;
      setPosition(next);
    } else if (cur.type === "youtube") {
      const times = ytGetTimes(cur.id);
      const next = Math.max(0, Math.min(times.duration, times.current + delta));
      ytSeekTo(cur.id, next);
      setPosition(next);
    }
  };

  const seekTo = (seconds: number) => {
    const cur = state.current;
    if (!cur) return;
    if (cur.type === "audio") {
      const el = audioRef.current;
      if (!el) return;
      el.currentTime = seconds;
      setPosition(seconds);
    } else if (cur.type === "youtube") {
      ytSeekTo(cur.id, seconds);
      setPosition(seconds);
    }
  };

  const next = () => {
    if (state.queue.length <= 1) return;
    const ni = Math.min(state.queue.length - 1, state.index + 1);
    const item = state.queue[ni];
    if (item.type === "audio") {
      const el = (item as any).el as HTMLAudioElement | null;
      if (el) void requestPlayAudio(el, { id: item.id, title: item.title });
    } else {
      void requestPlayYouTube(item.id, { title: item.title });
    }
    setState((s) => ({ ...s, index: ni }));
  };

  const prev = () => {
    if (state.queue.length <= 1) return;
    const pi = Math.max(0, state.index - 1);
    const item = state.queue[pi];
    if (item.type === "audio") {
      const el = (item as any).el as HTMLAudioElement | null;
      if (el) void requestPlayAudio(el, { id: item.id, title: item.title });
    } else {
      void requestPlayYouTube(item.id, { title: item.title });
    }
    setState((s) => ({ ...s, index: pi }));
  };

  // Keep position/duration updated for YouTube when active
  useEffect(() => {
    let interval: any;
    if (state.current?.type === "youtube") {
      interval = setInterval(() => {
        const t = ytGetTimes(state.current!.id);
        setPosition(t.current);
        setDuration(t.duration);
      }, 500);
    }
    return () => interval && clearInterval(interval);
  }, [state.current?.type, state.current && (state.current as any).id]);

  useEffect(() => {
    const nav: any = typeof navigator !== 'undefined' ? navigator : null;
    if (!nav || !('mediaSession' in nav)) return;
    const cur = state.current;
    if (!cur) {
      nav.mediaSession.metadata = null;
      return;
    }
    const title = cur.title || (cur.type === 'audio' ? cur.id : `YouTube ${cur.id}`);
    try {
      nav.mediaSession.metadata = new (window as any).MediaMetadata({ title });
    } catch {}
  }, [state.current]);

  useEffect(() => {
    const nav: any = typeof navigator !== 'undefined' ? navigator : null;
    if (!nav || !('mediaSession' in nav)) return;
    nav.mediaSession.playbackState = state.playing ? 'playing' : 'paused';
  }, [state.playing]);

  useEffect(() => {
    const nav: any = typeof navigator !== 'undefined' ? navigator : null;
    if (!nav || !('mediaSession' in nav)) return;
    if (typeof nav.mediaSession.setPositionState === 'function') {
      const dur = Number.isFinite(duration) ? duration : 0;
      const pos = Number.isFinite(position) ? position : 0;
      try { nav.mediaSession.setPositionState({ duration: Math.max(0, dur), playbackRate: 1, position: Math.max(0, pos) }); } catch {}
    }
  }, [position, duration, state.current && (state.current as any).id]);

  useEffect(() => {
    const nav: any = typeof navigator !== 'undefined' ? navigator : null;
    if (!nav || !('mediaSession' in nav)) return;
    try { nav.mediaSession.setActionHandler('play', () => toggle()); } catch {}
    try { nav.mediaSession.setActionHandler('pause', () => toggle()); } catch {}
    try { nav.mediaSession.setActionHandler('seekbackward', (e: any) => seekBy(-(e?.seekOffset || 10))); } catch {}
    try { nav.mediaSession.setActionHandler('seekforward', (e: any) => seekBy(e?.seekOffset || 10)); } catch {}
    try { nav.mediaSession.setActionHandler('previoustrack', () => prev()); } catch {}
    try { nav.mediaSession.setActionHandler('nexttrack', () => next()); } catch {}
    try { nav.mediaSession.setActionHandler('stop', () => stop()); } catch {}
  }, [toggle, seekBy, next, prev, stop]);

  const value = useMemo(
    () => ({ state, requestPlayAudio, requestPlayYouTube, toggle, pauseAll, stop, seekBy, seekTo, next, prev, position, duration }),
    [state, position, duration]
  );

  return <NowPlayingContext.Provider value={value}>{children}</NowPlayingContext.Provider>;
}

export function useNowPlaying() {
  const ctx = useContext(NowPlayingContext);
  if (!ctx) throw new Error("useNowPlaying must be used within NowPlayingProvider");
  return ctx;
}
