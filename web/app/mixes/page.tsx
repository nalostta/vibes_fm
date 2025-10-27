import MixCard from "@/components/MixCard";
import type { Mix } from "@/components/MixCard";
import KoiBackground from "@/components/KoiBackground";
import { getAllPosts, getCoverFromEmbed } from "@/lib/posts";

export default function MixesPage() {
  const posts = getAllPosts();
  const mixes: Mix[] = posts.map((p) => ({
    id: p.slug,
    title: p.title,
    description: p.content ? p.content.split("\n\n")[0] : undefined,
    cover: getCoverFromEmbed(p) ?? undefined,
    audioUrl: p.audioUrl ?? undefined,
    embed: p.embed ?? undefined,
    genre: p.tags?.[0],
    mood: p.tags?.[1],
    duration: undefined,
    releaseDate: p.date,
  }));

  return (
    <>
      <KoiBackground />
      <div className="relative">
        <div className="fixed inset-0 z-0 pointer-events-none bg-black/70 backdrop-blur-lg" />
        <main className="relative z-10 mx-auto max-w-6xl px-4 py-10">
          <h1 className="text-2xl font-semibold mb-6">All Mixes</h1>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {mixes.map((m) => (
              <MixCard key={m.id} mix={m} href={`/posts/${m.id}`} />
            ))}
          </div>
        </main>
      </div>
    </>
  );
}
