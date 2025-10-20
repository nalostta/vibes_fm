import Link from "next/link";
import MixCard from "@/components/MixCard";
import AudioPlayer from "@/components/AudioPlayer";
import { getAllPosts, getCoverFromEmbed } from "@/lib/posts";
import KoiBackground from "@/components/KoiBackground";
import type { Mix } from "@/components/MixCard";


export default function Home() {
  const posts = getAllPosts().slice(0, 6);
  const latestMix: Mix = {
    id: "latest",
    title: "Latest Mix — Midnight Drift",
    description: "A deep, late-night journey across house and ambient textures.",
    genre: "House",
    mood: "Chill",
    duration: "01:03:22",
  };

  // removed unused demo `featured` list

  const recentTracks = [
    "DJ Selek — Monika",
    "Kiasmos — Looped",
    "Bicep — Glue",
    "Bonobo — Cirrus",
  ];

  return (
    <>
      <KoiBackground />
      <div className="relative">
        <div className="fixed inset-0 z-0 pointer-events-none bg-black/70 backdrop-blur-lg" />
        <main className="relative z-10 mx-auto max-w-6xl px-4 py-10 space-y-14">
      <section className="grid gap-6 lg:grid-cols-2 items-start">
        <div className="space-y-5">
          <div className="inline-block rounded-full border border-white/20 bg-black/50 text-white px-3 py-1 text-xs tracking-wide">Latest Mix</div>
          <h1 className="text-3xl sm:text-5xl font-semibold leading-tight text-white drop-shadow-lg">VIBES.FM — Music Mixes & Tracklists</h1>
          <p className="text-white/70 text-sm sm:text-base max-w-prose">Curated musical journeys by Nalostta. Explore mixes across genres, moods, and vibes — stream, browse tracklists, and discover your next favorite sound.</p>
          <div className="flex gap-3">
            <Link href="/mixes" className="px-4 py-2 rounded bg-white text-black text-sm font-medium">Browse Mixes</Link>
            <Link href="/vibes" className="px-4 py-2 rounded border border-white/30 text-white text-sm">Current Vibes</Link>
          </div>
        </div>
        <div className="relative z-20 rounded-xl border border-white/10 bg-black p-5">
          <div className="aspect-video rounded-md bg-gradient-to-br from-purple-500/20 to-indigo-500/20 mb-4" />
          <h3 className="text-lg font-semibold mb-1 text-white">{latestMix.title}</h3>
          <p className="text-sm text-white/70 mb-4">{latestMix.description}</p>
          <AudioPlayer src={null} title={latestMix.title} />
        </div>
      </section>

      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">Featured Mixes</h2>
          <Link href="/mixes" className="text-sm text-white/70 hover:text-white">View all</Link>
        </div>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {posts.map((p) => {
            const desc = p.content ? p.content.split("\n\n")[0] : undefined;
            const mixLike: Mix = {
              id: p.slug,
              title: p.title,
              description: desc,
              cover: getCoverFromEmbed(p) ?? undefined,
              audioUrl: undefined,
              genre: p.tags?.[0],
              mood: p.tags?.[1],
              duration: undefined,
              releaseDate: p.date,
            };
            return <MixCard key={p.slug} mix={mixLike} href={`/posts/${p.slug}`} />;
          })}
        </div>
      </section>

      <section className="grid gap-8 lg:grid-cols-2">
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-white">Recently Added Tracks</h2>
          <ul className="space-y-2 text-sm text-white/80">
            {recentTracks.map((t, i) => (
              <li key={i} className="rounded border border-white/10 bg-black/30 px-3 py-2">{t}</li>
            ))}
          </ul>
        </div>
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-white">About</h2>
          <p className="text-sm text-white/80">Nalostta shares carefully crafted mixes spanning house, techno, ambient and beyond. Dive into detailed tracklists, explore moods, and follow along with new releases.</p>
          <Link href="/about" className="text-sm underline underline-offset-4 text-white hover:text-white">Read more</Link>
        </div>
      </section>

      <section className="rounded-xl border border-white/10 bg-black/40 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold">Subscribe to the newsletter</h3>
            <p className="text-xs text-white/70">Get updates on new mixes and playlists.</p>
          </div>
          <form className="flex w-full sm:w-auto gap-2">
            <input className="flex-1 sm:w-72 bg-black/50 border border-white/10 rounded px-3 py-2 text-sm outline-none focus:border-white/30" placeholder="you@example.com" type="email" required />
            <button type="submit" className="px-4 py-2 rounded bg-white text-black text-sm font-medium">Subscribe</button>
          </form>
        </div>
      </section>
        </main>
      </div>
    </>
  );
}
