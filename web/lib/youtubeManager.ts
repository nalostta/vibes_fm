let apiReadyPromise: Promise<void> | null = null;

function loadApi(): Promise<void> {
  if (apiReadyPromise) return apiReadyPromise;
  apiReadyPromise = new Promise<void>((resolve) => {
    if (typeof window === 'undefined') return resolve();
    if ((window as any).YT && (window as any).YT.Player) return resolve();
    const scriptId = 'yt-iframe-api';
    if (!document.getElementById(scriptId)) {
      const s = document.createElement('script');
      s.id = scriptId;
      s.src = 'https://www.youtube.com/iframe_api';
      document.body.appendChild(s);
    }
    const onReadyApi = () => resolve();
    if ((window as any).YT && (window as any).YT.Player) onReadyApi();
    else if (!(window as any).onYouTubeIframeAPIReady) (window as any).onYouTubeIframeAPIReady = onReadyApi;
  });
  return apiReadyPromise;
}

const players = new Map<string, any>();
const readyPromises = new Map<string, Promise<void>>();
const listeners = new Map<string, Set<(state: any) => void>>();

function getOrCreateContainer(videoId: string): HTMLElement {
  const id = `yt-offscreen-${videoId}`;
  let el = document.getElementById(id);
  if (!el) {
    el = document.createElement('div');
    el.id = id;
    el.style.width = '0';
    el.style.height = '0';
    el.style.overflow = 'hidden';
    el.style.position = 'absolute';
    el.style.left = '-9999px';
    document.body.appendChild(el);
  }
  return el;
}

export async function ensureYouTubePlayer(videoId: string): Promise<any> {
  if (players.has(videoId)) return players.get(videoId);
  await loadApi();
  const container = getOrCreateContainer(videoId);
  let resolveReady: () => void;
  const readyPromise = new Promise<void>((resolve) => { resolveReady = resolve; });
  readyPromises.set(videoId, readyPromise);
  const player = new (window as any).YT.Player(container, {
    height: '0',
    width: '0',
    videoId,
    playerVars: {
      playsinline: 1,
      modestbranding: 1,
      rel: 0,
      enablejsapi: 1,
      origin: typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : undefined,
    },
    events: {
      onReady: () => {
        const ls = listeners.get(videoId);
        ls?.forEach((fn) => fn({ type: 'ready' }));
        resolveReady!();
      },
      onStateChange: (e: any) => {
        const ls = listeners.get(videoId);
        ls?.forEach((fn) => fn({ type: 'state', data: e.data }));
      },
    },
  });
  players.set(videoId, player);
  await readyPromise;
  return player;
}

export function play(videoId: string) {
  const p = players.get(videoId);
  if (p && typeof p.playVideo === 'function') p.playVideo();
}

export function pause(videoId: string) {
  const p = players.get(videoId);
  if (p && typeof p.pauseVideo === 'function') p.pauseVideo();
}

export function getTimes(videoId: string): { current: number; duration: number } {
  const p = players.get(videoId);
  const current = p && typeof p.getCurrentTime === 'function' ? p.getCurrentTime() : 0;
  const duration = p && typeof p.getDuration === 'function' ? p.getDuration() : 0;
  return { current, duration };
}

export function seekTo(videoId: string, seconds: number) {
  const p = players.get(videoId);
  if (p && typeof p.seekTo === 'function') p.seekTo(seconds, true);
}

export function subscribe(videoId: string, fn: (evt: any) => void) {
  let set = listeners.get(videoId);
  if (!set) {
    set = new Set();
    listeners.set(videoId, set);
  }
  set.add(fn);
  return () => {
    set?.delete(fn);
  };
}
