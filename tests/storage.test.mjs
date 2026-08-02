import assert from "node:assert/strict";
import test from "node:test";

import {
  createStorage,
  storageInternals,
} from "../assets/js/storage.js";


function persistentPair() {
  const backend = storageInternals.createMemoryStorage();
  return {
    first: createStorage(backend),
    reload: () => createStorage(backend),
  };
}


test("favorites persist across a recreated storage facade", () => {
  const { first, reload } = persistentPair();
  assert.equal(first.toggleFavorite("yt-video-a"), true);
  assert.equal(first.toggleFavorite("yt-video-b", true), true);
  assert.deepEqual(reload().getFavorites(), new Set(["yt-video-a", "yt-video-b"]));
  assert.equal(reload().toggleFavorite("yt-video-a", false), false);
  assert.deepEqual(reload().getFavorites(), new Set(["yt-video-b"]));
});


test("watched state persists across a recreated storage facade", () => {
  const { first, reload } = persistentPair();
  first.toggleWatched("yt-watched", true);
  assert.deepEqual(reload().getWatched(), new Set(["yt-watched"]));
  reload().toggleWatched("yt-watched", false);
  assert.equal(reload().getWatched().size, 0);
});


test("learning-path progress persists and remains sorted", () => {
  const { first, reload } = persistentPair();
  first.setPathStep("beginner-offroad-adventure", 3, true);
  first.setPathStep("beginner-offroad-adventure", 1, true);
  assert.deepEqual(reload().getPathProgress(), {
    "beginner-offroad-adventure": [1, 3],
  });
  reload().setPathStep("beginner-offroad-adventure", 1, false);
  assert.deepEqual(reload().getPathProgress()["beginner-offroad-adventure"], [3]);
});


test("theme persists and rejects unsupported values", () => {
  const { first, reload } = persistentPair();
  first.setTheme("dark");
  assert.equal(reload().getTheme(), "dark");
  reload().setTheme("sepia");
  assert.equal(reload().getTheme(), null);
  reload().setTheme("light");
  assert.equal(reload().getTheme(), "light");
});


test("last viewed video persists for continue-watching", () => {
  const { first, reload } = persistentPair();
  first.setLastVideo("yt-last-video");
  const lastVideo = reload().getLastVideo();
  assert.equal(lastVideo.id, "yt-last-video");
  assert.ok(Number.isFinite(Date.parse(lastVideo.updatedAt)));
});
