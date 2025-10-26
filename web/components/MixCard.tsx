"use client";
import Link from "next/link";
import Image from "next/image";
import AudioPlayer from "@/components/AudioPlayer";
import YouTubeAudioPlayer from "@/components/YouTubeAudioPlayer";

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
  const renderMiniPlayer = () => {
    if (mix.audioUrl) {
      return <AudioPlayer src={mix.audioUrl} title={mix.title} />;
    }
    if (mix.embed?.type === "youtube") {
      // Render a custom audio-only controller backed by the YouTube IFrame API
      return <YouTubeAudioPlayer url={mix.embed.url} title={mix.title} />;
    }
    if (mix.embed?.type === "soundcloud") {
      // Use SoundCloud mini player
      const base = mix.embed.url;
      const sep = base.includes("?") ? "&" : "?";
      const opts = "visual=false&show_comments=false&hide_related=true&show_user=false&show_reposts=false&show_teaser=false&auto_play=false";
      return (
        <div className="w-full rounded border border-white/10 bg-black/30 p-2">
          <iframe
            title={mix.title}
            width="100%"
            height="64"
            scrolling="no"
            frameBorder="no"
            allow="autoplay"
            src={`${base}${sep}${opts}`}
          />
        </div>
      );
    }
    return <AudioPlayer src={null} title={mix.title} />;
  };
  const content = (
    <>
      <div className="relative aspect-video bg-black/40">
        {mix.cover ? (
          <Image src={mix.cover} alt={mix.title} fill className="object-cover" sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw" />
        ) : null}
      </div>
      <div className="p-4 space-y-3">
        <div>
          <h3 className="text-base font-semibold text-white">{mix.title}</h3>
          {mix.description ? (
            <p className="text-sm text-white/70 line-clamp-2">{mix.description}</p>
          ) : null}
        </div>
        <div
          onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
          onMouseDown={(e) => { e.stopPropagation(); }}
          onKeyDown={(e) => { e.stopPropagation(); }}
          role="group"
        >
          {renderMiniPlayer()}
        </div>
        <div className="text-xs text-white/70 flex gap-3">
          {mix.genre ? <span>#{mix.genre}</span> : null}
          {mix.mood ? <span>#{mix.mood}</span> : null}
          {mix.duration ? <span>{mix.duration}</span> : null}
        </div>
      </div>
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
