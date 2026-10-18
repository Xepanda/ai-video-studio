/**
 * scripts/bridge/chatcut_to_timeline.js
 * 
 * Converts OpenChatCut multi-track project schema back to Remotion's timeline.json.
 * Extracts voiceover track clips, re-creates scenes, preserves and shifts word timestamps if clips moved,
 * and runs sanitizeTimelineGaps before writing output.
 * 
 * CLI: node scripts/bridge/chatcut_to_timeline.js [inputProject] [outputTimeline]
 * Default input: public/chatcut_project.json
 * Default output: public/timeline.json
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { sanitizeTimelineGaps } = require('./timeline_sanitizer');

/**
 * Shifts word timestamps to maintain synchronization with clip startFrame and duration.
 * 
 * @param {Array<Object>} words - Array of word alignment objects
 * @param {number} clipStartFrame - The clip's startFrame on the timeline
 * @param {number} clipDuration - The clip's duration in frames
 * @returns {Array<Object>} Shifted words
 */
function shiftWordTimestamps(words, clipStartFrame, clipDuration) {
  if (!Array.isArray(words)) return [];

  return words.map(w => {
    const word = { ...w };

    // Derive local startFrame if only globalStartFrame is provided
    if (typeof word.startFrame !== 'number' && typeof word.globalStartFrame === 'number') {
      word.startFrame = Math.max(0, word.globalStartFrame - clipStartFrame);
    }
    // Derive local endFrame if only globalEndFrame is provided
    if (typeof word.endFrame !== 'number' && typeof word.globalEndFrame === 'number') {
      word.endFrame = Math.max(word.startFrame || 0, word.globalEndFrame - clipStartFrame);
    }

    // Default fallbacks if startFrame/endFrame are missing
    if (typeof word.startFrame !== 'number') {
      word.startFrame = 0;
    }
    if (typeof word.endFrame !== 'number') {
      word.endFrame = clipDuration || 0;
    }

    // Update globalStartFrame and globalEndFrame based on clip's position
    word.globalStartFrame = clipStartFrame + word.startFrame;
    word.globalEndFrame = clipStartFrame + word.endFrame;

    return word;
  });
}

/**
 * Converts an OpenChatCut multi-track project object back to Remotion timeline.json schema.
 * 
 * @param {Object} project - OpenChatCut project object
 * @returns {Object} Remotion timeline object
 */
function chatcutToTimeline(project) {
  if (!project || typeof project !== 'object') {
    throw new Error('Invalid project: expected an object');
  }

  const tracks = Array.isArray(project.tracks) ? project.tracks : [];
  const voiceTrack = tracks.find(t => t.id === 'track-voiceover') || tracks.find(t => t.type === 'audio');
  const brollTrack = tracks.find(t => t.id === 'track-broll') || tracks.find(t => t.type === 'video');
  const subtitlesTrack = tracks.find(t => t.id === 'track-subtitles') || tracks.find(t => t.type === 'subtitles');

  const voiceClips = voiceTrack && Array.isArray(voiceTrack.clips)
    ? [...voiceTrack.clips]
    : [];

  // Sort clips chronologically by startFrame
  voiceClips.sort((a, b) => (a.startFrame ?? 0) - (b.startFrame ?? 0));

  // Re-create scenes from clips
  const rawScenes = voiceClips.map(clip => {
    const brollClip = brollTrack && Array.isArray(brollTrack.clips)
      ? brollTrack.clips.find(c => c.id === `broll-${clip.id}` || c.id === clip.id)
      : null;

    const subClip = subtitlesTrack && Array.isArray(subtitlesTrack.clips)
      ? subtitlesTrack.clips.find(c => c.id === `sub-${clip.id}` || c.id === clip.id)
      : null;

    const clipStart = clip.startFrame ?? 0;
    const clipDuration = clip.durationInFrames ?? 0;

    const inputWords = (Array.isArray(clip.words) && clip.words.length > 0)
      ? clip.words
      : (subClip && Array.isArray(subClip.words) ? subClip.words : []);

    const shiftedWords = shiftWordTimestamps(inputWords, clipStart, clipDuration);

    const { source, ...clipRest } = clip;
    const scene = {
      ...clipRest,
      id: clip.id,
      type: clip.type || 'MinimalHeadline',
      startFrame: clipStart,
      durationInFrames: clipDuration,
      audioPath: clip.source || clip.audioPath || '',
      text: clip.text || (subClip ? subClip.text : '') || '',
      words: shiftedWords,
      emotion: clip.emotion || '<|NEUTRAL|>'
    };

    if (clip.brollPath) {
      scene.brollPath = clip.brollPath;
    } else if (brollClip && brollClip.source && brollClip.source !== `footage/${clip.id}.mp4`) {
      scene.brollPath = brollClip.source;
    }

    return scene;
  });

  // Run sanitizeTimelineGaps before producing output
  const { sanitizedScenes, totalDurationInFrames } = sanitizeTimelineGaps(rawScenes);

  // Synchronize global word timestamps with finalized scene start frames
  sanitizedScenes.forEach(scene => {
    if (Array.isArray(scene.words)) {
      scene.words.forEach(w => {
        if (typeof w.startFrame === 'number') {
          w.globalStartFrame = (scene.startFrame ?? 0) + w.startFrame;
        }
        if (typeof w.endFrame === 'number') {
          w.globalEndFrame = (scene.startFrame ?? 0) + w.endFrame;
        }
      });
    }
  });

  // Preserve all metadata from the original project
  const { tracks: _discardTracks, ...projectMeta } = project;

  const timeline = {
    ...projectMeta,
    fps: project.fps || 30,
    totalDurationInFrames: totalDurationInFrames,
    scenes: sanitizedScenes
  };

  return timeline;
}

/**
 * File-level converter from OpenChatCut project JSON to Remotion timeline JSON.
 * 
 * @param {string} inputPath 
 * @param {string} outputPath 
 * @returns {Object} Converted timeline
 */
function convertChatcutToTimelineFile(inputPath, outputPath) {
  const resolvedInput = path.resolve(process.cwd(), inputPath);
  const resolvedOutput = path.resolve(process.cwd(), outputPath);

  if (!fs.existsSync(resolvedInput)) {
    throw new Error(`Input project file not found at: ${resolvedInput}`);
  }

  const raw = fs.readFileSync(resolvedInput, 'utf-8');
  const project = JSON.parse(raw);
  const timeline = chatcutToTimeline(project);

  const outputDir = path.dirname(resolvedOutput);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(resolvedOutput, JSON.stringify(timeline, null, 2), 'utf-8');
  return timeline;
}

// CLI Execution entrypoint
if (require.main === module) {
  const args = process.argv.slice(2);
  const inputArg = args[0] || 'public/chatcut_project.json';
  const outputArg = args[1] || 'public/timeline.json';

  try {
    console.log(`[Bridge] Converting OpenChatCut project -> Remotion timeline...`);
    console.log(`  Input:  ${inputArg}`);
    console.log(`  Output: ${outputArg}`);

    const timeline = convertChatcutToTimelineFile(inputArg, outputArg);

    console.log(`[Bridge] Conversion successful!`);
    console.log(`  FPS: ${timeline.fps}`);
    console.log(`  Total Duration (frames): ${timeline.totalDurationInFrames}`);
    console.log(`  Scenes: ${timeline.scenes.length}`);
    timeline.scenes.forEach((s, idx) => {
      console.log(`    - [${s.id}] ${s.type} (start: ${s.startFrame}, dur: ${s.durationInFrames})`);
    });
  } catch (err) {
    console.error(`[Bridge Error] Failed to convert chatcut project:`, err.message);
    process.exit(1);
  }
}

module.exports = {
  chatcutToTimeline,
  convertChatcutToTimelineFile,
  shiftWordTimestamps
};
