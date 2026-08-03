/**
 * Builds an in-memory scalability fixture from verified source records.
 * Generated identities exist only for the lifetime of the test process.
 */
export function buildVideoFixture(sourceVideos, targetCount) {
  if (!Array.isArray(sourceVideos) || sourceVideos.length === 0) {
    throw new TypeError("sourceVideos must be a non-empty array");
  }
  if (!Number.isInteger(targetCount) || targetCount <= 0) {
    throw new TypeError("targetCount must be a positive integer");
  }
  if (targetCount < sourceVideos.length) {
    throw new RangeError("targetCount cannot be smaller than the verified source dataset");
  }

  const fixture = structuredClone(sourceVideos);
  const usedYouTubeIds = new Set(fixture.map((video) => video.youtube_video_id));
  let sequence = 1;

  while (fixture.length < targetCount) {
    const source = sourceVideos[(fixture.length - sourceVideos.length) % sourceVideos.length];
    let youtubeId;
    do {
      youtubeId = `fx${String(sequence).padStart(9, "0")}`;
      sequence += 1;
    } while (usedYouTubeIds.has(youtubeId));
    usedYouTubeIds.add(youtubeId);

    fixture.push({
      ...structuredClone(source),
      id: `yt-${youtubeId}`,
      youtube_video_id: youtubeId,
      youtube_url: `https://www.youtube.com/watch?v=${youtubeId}`,
      thumbnail_url: `https://i.ytimg.com/vi/${youtubeId}/hqdefault.jpg`,
    });
  }

  return fixture;
}
