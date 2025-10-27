import Link from "next/link";

type Props = {
  slug: string;
  title: string;
  date?: string;
  postType: "individual_track" | "DJ-Set" | "set_remake" | "music_mashup";
  tags?: string[];
  cover?: string;
};

const typeLabel: Record<Props["postType"], string> = {
  individual_track: "Track",
  DJ-Set: "DJ Set",
  set_remake: "Set Remake",
  music_mashup: "Mashup",
};

export default function PostTile({ slug, title, date, postType, tags, cover }: Props) {
  return (
    <Link
      href={`/posts/${slug}`}
      className="block rounded-lg border border-white/10 bg-black/40 hover:bg-black/50 transition-colors overflow-hidden"
    >
      {cover ? (
        <div className="aspect-video w-full bg-black/30">
          {/* Using img to keep this lightweight for static export */}
          <img
            src={cover}
            alt={title}
            className="h-full w-full object-cover"
            loading="lazy"
          />
        </div>
      ) : null}
      <div className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[10px] uppercase tracking-wide rounded px-2 py-1 border border-white/10 bg-black/40 text-white/70">
            {typeLabel[postType]}
          </span>
          {date ? <span className="text-xs text-white/70">{new Date(date).toLocaleDateString()}</span> : null}
        </div>
        <h3 className="text-base font-semibold line-clamp-2">{title}</h3>
        {tags && tags.length ? (
          <div className="flex flex-wrap gap-2">
            {tags.map((t) => (
              <span key={t} className="text-xs text-white/70">#{t}</span>
            ))}
          </div>
        ) : null}
      </div>
    </Link>
  );
}
