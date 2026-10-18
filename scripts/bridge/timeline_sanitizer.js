/**
 * scripts/bridge/timeline_sanitizer.js
 * 
 * Provides timeline gap and overlap sanitization to prevent Remotion black flicker,
 * and continuity validation for multi-scene video timelines.
 */

'use strict';

/**
 * Validates the continuity of scenes in a timeline.
 * Ensures each scene starts exactly where the previous scene ended.
 * 
 * @param {Array<Object>} scenes - Array of scene objects
 * @returns {{ isValid: boolean, valid: boolean, errors: Array<string> }}
 */
function validateSceneContinuity(scenes) {
  const errors = [];
  if (!Array.isArray(scenes) || scenes.length === 0) {
    return { isValid: true, valid: true, errors: [] };
  }

  let expectedFrame = 0;
  for (let i = 0; i < scenes.length; i++) {
    const scene = scenes[i];
    const sceneId = scene.id || `scene_${i + 1}`;
    const startFrame = scene.startFrame ?? 0;
    const duration = scene.durationInFrames ?? 0;

    if (startFrame !== expectedFrame) {
      errors.push(
        `Scene [${sceneId}] non-continuous startFrame! Expected: ${expectedFrame}, Actual: ${startFrame} (diff: ${startFrame - expectedFrame})`
      );
    }
    expectedFrame = startFrame + duration;
  }

  return {
    isValid: errors.length === 0,
    valid: errors.length === 0,
    errors
  };
}

/**
 * Sanitizes gaps and overlaps between adjacent scenes.
 * 
 * - If diff = nextScene.startFrame - (currentScene.startFrame + currentScene.durationInFrames)
 * - If Math.abs(diff) <= 3 (and diff !== 0), automatically snaps currentScene.durationInFrames += diff
 *   to close 1-3 frame gaps/overlaps (prevents Remotion black flicker).
 * - If diff > 3, inserts a filler scene with dark background:
 *   { id: `filler_${idx}`, type: 'Filler', startFrame: currentScene.startFrame + currentScene.durationInFrames, durationInFrames: diff, isFiller: true }
 * - If diff < -3, snaps currentScene.durationInFrames to nextScene.startFrame - currentScene.startFrame.
 * 
 * @param {Array<Object>} scenes - Array of scene objects
 * @returns {{ sanitizedScenes: Array<Object>, totalDurationInFrames: number, gapFixesCount: number, isValid: boolean, validationErrors: Array<string> }}
 */
function sanitizeTimelineGaps(scenes) {
  if (!Array.isArray(scenes) || scenes.length === 0) {
    return {
      sanitizedScenes: [],
      totalDurationInFrames: 0,
      gapFixesCount: 0,
      isValid: true,
      validationErrors: []
    };
  }

  // Deep clone scenes to prevent unintended side effects on caller's objects
  const cloned = scenes.map(scene => ({
    ...scene,
    words: Array.isArray(scene.words) ? scene.words.map(w => ({ ...w })) : []
  }));

  let gapFixesCount = 0;
  let fillerIdx = 0;
  const result = [];

  // Handle leading gap if first scene does not start at 0
  if (cloned.length > 0 && cloned[0].startFrame !== 0) {
    const startDiff = cloned[0].startFrame;
    if (Math.abs(startDiff) <= 3) {
      cloned[0].startFrame = 0;
      cloned[0].durationInFrames += startDiff;
      gapFixesCount++;
    } else if (startDiff > 3) {
      result.push({
        id: `filler_${fillerIdx++}`,
        type: 'Filler',
        startFrame: 0,
        durationInFrames: startDiff,
        isFiller: true,
        text: '',
        words: []
      });
      gapFixesCount++;
    }
  }

  for (let i = 0; i < cloned.length; i++) {
    const currentScene = cloned[i];
    result.push(currentScene);

    if (i < cloned.length - 1) {
      const nextScene = cloned[i + 1];
      const currentEnd = currentScene.startFrame + currentScene.durationInFrames;
      const diff = nextScene.startFrame - currentEnd;

      if (diff !== 0 && Math.abs(diff) <= 3) {
        // Automatically snap duration to close 1-3 frame gaps or overlaps
        currentScene.durationInFrames += diff;
        gapFixesCount++;
      } else if (diff > 3) {
        // Insert filler scene for gaps larger than 3 frames
        const filler = {
          id: `filler_${fillerIdx++}`,
          type: 'Filler',
          startFrame: currentScene.startFrame + currentScene.durationInFrames,
          durationInFrames: diff,
          isFiller: true,
          text: '',
          words: []
        };
        result.push(filler);
        gapFixesCount++;
      } else if (diff < -3) {
        // Severe overlap (> 3 frames): snap currentScene duration to eliminate overlap
        currentScene.durationInFrames = Math.max(0, nextScene.startFrame - currentScene.startFrame);
        gapFixesCount++;
      }
    }
  }

  // Update words timestamps and clamp word endFrame if scene duration was shrunk
  result.forEach(scene => {
    if (Array.isArray(scene.words)) {
      scene.words.forEach(w => {
        if (typeof w.endFrame === 'number' && typeof scene.durationInFrames === 'number' && w.endFrame > scene.durationInFrames) {
          w.endFrame = scene.durationInFrames;
        }
        if (typeof w.startFrame === 'number') {
          w.globalStartFrame = (scene.startFrame ?? 0) + w.startFrame;
        }
        if (typeof w.endFrame === 'number') {
          w.globalEndFrame = (scene.startFrame ?? 0) + w.endFrame;
        }
      });
    }
  });

  // Calculate totalDurationInFrames from the last scene
  let totalDurationInFrames = 0;
  if (result.length > 0) {
    const lastScene = result[result.length - 1];
    totalDurationInFrames = (lastScene.startFrame ?? 0) + (lastScene.durationInFrames ?? 0);
  }

  const validation = validateSceneContinuity(result);

  return {
    sanitizedScenes: result,
    totalDurationInFrames,
    gapFixesCount,
    isValid: validation.isValid,
    validationErrors: validation.errors
  };
}

module.exports = {
  sanitizeTimelineGaps,
  validateSceneContinuity
};
