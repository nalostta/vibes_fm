"use client";
import Link from "next/link";
import Image from "next/image";
import { useRef } from "react";
import { useNowPlaying } from "@/components/NowPlayingContext";

export type Mix = {
  id: string;
  title: string;
  description?: string;
  cover?: string;
  audioUrl?: string;
  embed?: { type: "youtube" | "soundcloud"; url: string };
  genre?: string;
  mood?: string;
  duration?: string;
  releaseDate?: string;
};

type Props = { mix: Mix; href?: string };

export default function MixCard({ mix, href }: Props) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const { requestPlayAudio, requestPlayYouTube } = useNowPlaying();

  const getYouTubeId = (url?: string) => {
    if (!url) return null;
    try {
      const u = new URL(url);
      if (u.hostname === "youtu.be") return u.pathname.slice(1);
      if (u.searchParams.get("v")) return u.searchParams.get("v");
      // Fallback for embed URLs
      const parts = u.pathname.split("/").filter(Boolean);
      const i = parts.findIndex((p) => p === "embed");
      if (i >= 0 && parts[i + 1]) return parts[i + 1];
    } catch {}
    return null;
  };

  const onPlay = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (mix.audioUrl) {
      const el = audioRef.current;
      if (!el) return;
      // Ensure src set before play
      if (el.src !== mix.audioUrl) el.src = mix.audioUrl;
      el.preload = "metadata";
      await requestPlayAudio(el, { id: mix.audioUrl, title: mix.title });
      return;
    }
    if (mix.embed?.type === "youtube") {
      const vid = getYouTubeId(mix.embed.url);
      if (vid) await requestPlayYouTube(vid, { title: mix.title });
      return;
    }
    // For other types (e.g., SoundCloud), fall back to navigating to the detail page if provided
  };
  const content = (
    <>
      <div className="relative aspect-video bg-black/40 group">
        {mix.cover ? (
          <Image src={mix.cover} alt={mix.title} fill className="object-cover" sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw" />
        ) : null}
        {/* Fast rectangular overlay with highlighted play button */}
        <button
          onClick={onPlay}
          aria-label="Play"
          className="absolute inset-0 flex items-center justify-center focus:outline-none"
        >
          {/* Rectangle overlay (no blur/shadow for perf) */}
          <span
            className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-opacity duration-100"
            style={{ willChange: "opacity" }}
            aria-hidden
          />
          {/* Square play button */}
          <span
            className="relative inline-flex items-center justify-center rounded-md bg-white/90 text-black px-4 py-2 text-xl opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-[opacity,transform] duration-100 group-hover:scale-105 group-focus:scale-105"
            aria-hidden
          >
            ►
          </span>
        </button>
      </div>
      <div className="p-4 space-y-3">
        <div>
          <h3 className="text-base font-semibold text-white">{mix.title}</h3>
          {mix.description ? (
            <p className="text-sm text-white/70 line-clamp-2">{mix.description}</p>
          ) : null}
        </div>
        <div className="text-xs text-white/70 flex gap-3">
          {mix.genre ? <span>#{mix.genre}</span> : null}
          {mix.mood ? <span>#{mix.mood}</span> : null}
          {mix.duration ? <span>{mix.duration}</span> : null}
        </div>
      </div>
      {/* Hidden audio element used to drive playback via NowPlayingContext */}
      {mix.audioUrl ? (
        <audio ref={audioRef} src={mix.audioUrl} preload="metadata" className="hidden" />
      ) : null}
    </>
  );

  return href ? (
    <Link href={href} className="rounded-lg overflow-hidden border border-white/10 bg-black/40 hover:bg-black/50 transition-colors block">
      {content}
    </Link>
  ) : (
    <div className="rounded-lg overflow-hidden border border-white/10 bg-black/40">{content}</div>
  );
}
