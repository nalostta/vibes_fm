'use client';

export default function Footer() {
  return (
    <footer className="border-t border-white/10 mt-10">
      <div className="mx-auto max-w-6xl px-4 py-6 text-xs text-white/70 flex items-center justify-between">
        <p>© {new Date().getFullYear()} Nalostta — VIBES.FM</p>
        <div className="flex gap-3">
          <a className="hover:text-white" href="#" aria-label="Twitter">Twitter</a>
          <a className="hover:text-white" href="#" aria-label="Instagram">Instagram</a>
          <a className="hover:text-white" href="#" aria-label="Contact">Contact</a>
        </div>
      </div>
    </footer>
  );
}
