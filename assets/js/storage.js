export const STORAGE_KEYS = Object.freeze({
  favorites: "adv-guide:v1:favorites",
  watched: "adv-guide:v1:watched",
  pathProgress: "adv-guide:v1:path-progress",
  theme: "adv-guide:v1:theme",
  lastVideo: "adv-guide:v1:last-video",
});

function safeParse(value, fallback) {
  if (typeof value !== "string" || value === "") return fallback;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function availableStorage(candidate) {
  if (!candidate) return null;
  try {
    const probe = "adv-guide:storage-probe";
    candidate.setItem(probe, "1");
    candidate.removeItem(probe);
    return candidate;
  } catch {
    return null;
  }
}

function createMemoryStorage() {
  const values = new Map();
  return {
    getItem(key) {
      return values.has(key) ? values.get(key) : null;
    },
    setItem(key, value) {
      values.set(key, String(value));
    },
    removeItem(key) {
      values.delete(key);
    },
    clear() {
      values.clear();
    },
  };
}

export function createStorage(candidate) {
  const backend = availableStorage(candidate) || createMemoryStorage();

  function readSet(key) {
    const parsed = safeParse(backend.getItem(key), []);
    return new Set(Array.isArray(parsed) ? parsed.filter((item) => typeof item === "string") : []);
  }

  function writeSet(key, values) {
    backend.setItem(key, JSON.stringify([...values].sort()));
  }

  function toggleSetItem(key, id, force) {
    const values = readSet(key);
    const shouldAdd = typeof force === "boolean" ? force : !values.has(id);
    if (shouldAdd) values.add(id);
    else values.delete(id);
    writeSet(key, values);
    return shouldAdd;
  }

  return {
    backend,

    getFavorites() {
      return readSet(STORAGE_KEYS.favorites);
    },
    toggleFavorite(id, force) {
      return toggleSetItem(STORAGE_KEYS.favorites, id, force);
    },

    getWatched() {
      return readSet(STORAGE_KEYS.watched);
    },
    toggleWatched(id, force) {
      return toggleSetItem(STORAGE_KEYS.watched, id, force);
    },

    getPathProgress() {
      const parsed = safeParse(backend.getItem(STORAGE_KEYS.pathProgress), {});
      if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") return {};
      return Object.fromEntries(
        Object.entries(parsed).map(([pathId, stepIds]) => [
          pathId,
          Array.isArray(stepIds) ? [...new Set(stepIds.filter(Number.isInteger))].sort((a, b) => a - b) : [],
        ]),
      );
    },
    setPathStep(pathId, stepOrder, complete) {
      const progress = this.getPathProgress();
      const steps = new Set(progress[pathId] || []);
      if (complete) steps.add(stepOrder);
      else steps.delete(stepOrder);
      progress[pathId] = [...steps].sort((a, b) => a - b);
      backend.setItem(STORAGE_KEYS.pathProgress, JSON.stringify(progress));
      return progress[pathId];
    },

    getTheme() {
      const theme = backend.getItem(STORAGE_KEYS.theme);
      return theme === "light" || theme === "dark" ? theme : null;
    },
    setTheme(theme) {
      if (theme === "light" || theme === "dark") backend.setItem(STORAGE_KEYS.theme, theme);
      else backend.removeItem(STORAGE_KEYS.theme);
    },

    getLastVideo() {
      const parsed = safeParse(backend.getItem(STORAGE_KEYS.lastVideo), null);
      if (!parsed || typeof parsed.id !== "string") return null;
      return parsed;
    },
    setLastVideo(id) {
      backend.setItem(STORAGE_KEYS.lastVideo, JSON.stringify({ id, updatedAt: new Date().toISOString() }));
    },
  };
}

function getWindowLocalStorage() {
  try {
    return typeof window !== "undefined" ? window.localStorage : null;
  } catch {
    return null;
  }
}

export const browserStorage = createStorage(getWindowLocalStorage());

export const storageInternals = Object.freeze({ safeParse, createMemoryStorage, getWindowLocalStorage });
