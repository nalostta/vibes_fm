import { getPostBySlug, getAllPosts } from "@/lib/posts";
import { notFound } from "next/navigation";

export const dynamicParams = false;

function Embed({ type, url }: { type: "youtube" | "soundcloud"; url: string }) {
  if (type === "youtube") {
    return (
      <div className="aspect-video w-full overflow-hidden rounded-md border border-white/10 bg-black/40">
        <iframe
          className="w-full h-full"
          src={url}
          title="YouTube player"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
        />
      </div>
    );
  }
  return (
    <div className="w-full overflow-hidden rounded-md border border-white/10 bg-black/40">
      <iframe
        width="100%"
        height="166"
        scrolling="no"
        frameBorder="no"
        allow="autoplay"
        src={url}
      />
    </div>
  );
}

// Generate static params at build time
export async function generateStaticParams() {
  const posts = getAllPosts();
  return posts.map((post) => ({
    slug: post.slug,
  }));
}

export default function PostPage({ params }: { params: { slug: string } }) {
  const post = getPostBySlug(params.slug);
  if (!post) return notFound();

  return (
    <main className="mx-auto max-w-3xl px-4 py-10 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[10px] uppercase tracking-wide rounded px-2 py-1 border border-white/10 bg-black/40 text-white/70">
            {post.postType.replace(/_/g, " ")}
          </span>
          {post.tags?.map((t) => (
            <span key={t} className="text-xs text-white/70">#{t}</span>
          ))}
        </div>
        <span className="text-xs text-white/50">{new Date(post.date).toLocaleDateString()}</span>
      </div>

      <h1 className="text-2xl sm:text-3xl font-semibold">{post.title}</h1>

      {post.embed ? <Embed type={post.embed.type} url={post.embed.url} /> : null}

      {post.tracklist && post.tracklist.length ? (
        <section className="space-y-2">
          <h2 className="text-lg font-semibold">Tracklist</h2>
          <ol className="list-decimal list-inside text-sm text-white/80 space-y-1">
            {post.tracklist.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ol>
        </section>
      ) : null}

      {post.content ? (
        <article className="prose prose-invert max-w-none text-white/90">
          {post.content.split('\n\n').map((para, i) => (
            <p key={i}>{para}</p>
          ))}
        </article>
      ) : null}
    </main>
  );
}
