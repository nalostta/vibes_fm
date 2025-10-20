import fs from "fs";
import path from "path";

export type PostFrontmatter = {
  title: string;
  slug: string;
  date: string; // ISO string
  postType: "individual_track" | "dj_set" | "set_remake" | "music_mashup";
  tags?: string[];
  embed?: { type: "youtube" | "soundcloud"; url: string } | null;
  tracklist?: string[];
  cover?: string; // optional custom cover image
};

export type Post = PostFrontmatter & {
  content: string;
};

const postsDir = path.join(process.cwd(), "content", "posts");

function parseMarkdown(raw: string): { frontmatter: PostFrontmatter; content: string } {
  const fmMatch = raw.match(/^---\n([\s\S]*?)\n---\n?/);
  if (!fmMatch) {
    throw new Error("Missing frontmatter block in markdown post");
  }
  const fmJson = fmMatch[1];
  let frontmatter: PostFrontmatter;
  try {
    frontmatter = JSON.parse(fmJson);
  } catch (e) {
    throw new Error("Invalid JSON frontmatter: " + (e as Error).message);
  }
  const content = raw.slice(fmMatch[0].length).trim();
  return { frontmatter, content };
}

export function getCoverFromEmbed(post: PostFrontmatter): string | null {
  if (post.cover) return post.cover;
  if (post.embed?.type === "youtube") {
    // Expect embed url like https://www.youtube.com/embed/<VIDEO_ID>
    const match = post.embed.url.match(/\/embed\/([a-zA-Z0-9_-]{6,})/);
    const id = match?.[1];
    if (id) return `https://i.ytimg.com/vi/${id}/hqdefault.jpg`;
  }
  // SoundCloud thumbnails would require API; return null unless provided via cover
  return null;
}

export function getAllPosts(): Post[] {
  if (!fs.existsSync(postsDir)) return [];
  const files = fs.readdirSync(postsDir).filter((f) => f.endsWith(".md"));
  const posts: Post[] = files.map((file) => {
    const raw = fs.readFileSync(path.join(postsDir, file), "utf-8");
    const { frontmatter, content } = parseMarkdown(raw);
    return { ...frontmatter, content };
  });
  return posts.sort((a, b) => (a.date < b.date ? 1 : -1));
}

export function getPostBySlug(slug: string): Post | null {
  const files = fs.existsSync(postsDir) ? fs.readdirSync(postsDir).filter((f) => f.endsWith(".md")) : [];
  for (const file of files) {
    const raw = fs.readFileSync(path.join(postsDir, file), "utf-8");
    const { frontmatter, content } = parseMarkdown(raw);
    if (frontmatter.slug === slug) {
      return { ...frontmatter, content };
    }
  }
  return null;
}
