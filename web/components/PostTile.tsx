import Link from "next/link";

type Props = {
  slug: string;
  title: string;
  date?: string;
  postType: "individual_track" | "dj_set" | "set_remake" | "music_mashup";
  tags?: string[];
};

const typeLabel: Record<Props["postType"], string> = {
  individual_track: "Track",
  dj_set: "DJ Set",
  set_remake: "Set Remake",
  music_mashup: "Mashup",
};

export default function PostTile({ slug, title, date, postType, tags }: Props) {
  return (
    <Link
      href={`/posts/${slug}`}
      className="block rounded-lg border border-white/10 bg-black/40 hover:bg-black/50 transition-colors p-4 space-y-3"
    >
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
    </Link>
  );
}
