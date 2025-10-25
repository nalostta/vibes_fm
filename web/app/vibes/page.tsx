import KoiBackground from "@/components/KoiBackground";

export default function VibesPage() {
  const tracks = [
    { title: "Track One — Artist A" },
    { title: "Track Two — Artist B" },
    { title: "Track Three — Artist C" },
  ];

  return (
    <>
      <KoiBackground />
      <div className="relative">
        <div className="fixed inset-0 z-0 pointer-events-none bg-black/70 backdrop-blur-lg" />
        <main className="relative z-10 mx-auto max-w-6xl px-4 py-10">
          <h1 className="text-2xl font-semibold mb-6">Current Vibes</h1>
          <ul className="space-y-2 text-sm">
            {tracks.map((t, idx) => (
              <li key={idx} className="rounded border border-white/10 bg-white/5 px-3 py-2">
                {t.title}
              </li>
            ))}
          </ul>
        </main>
      </div>
    </>
  );
}
