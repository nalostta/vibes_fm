import MixCard from "@/components/MixCard";
import KoiBackground from "@/components/KoiBackground";

const demoMixes = [
  { id: "1", title: "Sunset House Vol. 1", genre: "House", mood: "Chill", duration: "1:02:15" },
  { id: "2", title: "Deep Tech Journey", genre: "Techno", mood: "Focus", duration: "58:12" },
  { id: "3", title: "Ambient Drift", genre: "Ambient", mood: "Calm", duration: "45:21" },
];

export default function MixesPage() {
  return (
    <>
      <KoiBackground />
      <div className="relative">
        <div className="fixed inset-0 z-0 pointer-events-none bg-black/70 backdrop-blur-lg" />
        <main className="relative z-10 mx-auto max-w-6xl px-4 py-10">
          <h1 className="text-2xl font-semibold mb-6">All Mixes</h1>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {demoMixes.map((m) => (
              <MixCard key={m.id} mix={m} />
            ))}
          </div>
        </main>
      </div>
    </>
  );
}
