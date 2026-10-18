/**
 * scripts/bridge/timeline_to_chatcut.js
 * 
 * Converts Remotion timeline.json into OpenChatCut multi-track project schema.
 * CLI: node scripts/bridge/timeline_to_chatcut.js [inputTimeline] [outputProject]
 * Default input: public/timeline.json
 * Default output: public/chatcut_project.json
 */

'use strict';

const fs = require('fs');
const path = require('path');

/**
 * Converts a Remotion timeline object into an OpenChatCut multi-track project object.
 * 
 * @param {Object} timeline - Remotion timeline object
 * @returns {Object} OpenChatCut multi-track project object
 */
function timelineToChatcut(timeline) {
  if (!timeline || typeof timeline !== 'object') {
    throw new Error('Invalid timeline: expected an object');
  }

  const fps = typeof timeline.fps === 'number' ? timeline.fps : 30;
  const scenes = Array.isArray(timeline.scenes) ? timeline.scenes : [];
  const totalDurationInFrames = typeof timeline.totalDurationInFrames === 'number'
    ? timeline.totalDurationInFrames
    : scenes.reduce((sum, s) => sum + (s.durationInFrames || 0), 0);

  // 1. Track: Voiceover (GPT-SoVITS)
  const voiceoverClips = scenes.map(scene => {
    return {
      ...scene,
      id: scene.id,
      startFrame: scene.startFrame ?? 0,
      durationInFrames: scene.durationInFrames ?? 0,
      source: scene.audioPath || '',
      text: scene.text || '',
      words: Array.isArray(scene.words) ? scene.words.map(w => ({ ...w })) : [],
      emotion: scene.emotion || '<|NEUTRAL|>'
    };
  });

  const voiceoverTrack = {
    id: 'track-voiceover',
    type: 'audio',
    name: 'Voiceover (GPT-SoVITS)',
    volume: typeof timeline.voiceVolume === 'number' ? timeline.voiceVolume : 1.0,
    clips: voiceoverClips
  };

  // 2. Track: B-Roll Visuals
  const brollClips = scenes.map(scene => {
    const source = scene.brollPath || scene.heroVideo || scene.heroImage || `footage/${scene.id}.mp4`;
    return {
      id: `broll-${scene.id}`,
      startFrame: scene.startFrame ?? 0,
      durationInFrames: scene.durationInFrames ?? 0,
      source: source
    };
  });

  const brollTrack = {
    id: 'track-broll',
    type: 'video',
    name: 'B-Roll Visuals',
    clips: brollClips
  };

  // 3. Track: Dynamic Subtitles
  const subtitleClips = scenes.map(scene => {
    return {
      id: `sub-${scene.id}`,
      startFrame: scene.startFrame ?? 0,
      durationInFrames: scene.durationInFrames ?? 0,
      text: scene.text || '',
      words: Array.isArray(scene.words) ? scene.words.map(w => ({ ...w })) : []
    };
  });

  const subtitlesTrack = {
    id: 'track-subtitles',
    type: 'subtitles',
    name: 'Dynamic Subtitles',
    clips: subtitleClips
  };

  // Retain all top-level timeline metadata (project, theme, bgm configuration, etc.)
  const { scenes: _discardScenes, ...timelineMeta } = timeline;

  const project = {
    ...timelineMeta,
    fps: fps,
    totalDurationInFrames: totalDurationInFrames,
    tracks: [
      voiceoverTrack,
      brollTrack,
      subtitlesTrack
    ]
  };

  return project;
}

/**
 * File-level converter from timeline JSON to OpenChatCut project JSON.
 * 
 * @param {string} inputPath 
 * @param {string} outputPath 
 * @returns {Object} Converted project
 */
function convertTimelineToChatcutFile(inputPath, outputPath) {
  const resolvedInput = path.resolve(process.cwd(), inputPath);
  const resolvedOutput = path.resolve(process.cwd(), outputPath);

  if (!fs.existsSync(resolvedInput)) {
    throw new Error(`Input timeline file not found at: ${resolvedInput}`);
  }

  const raw = fs.readFileSync(resolvedInput, 'utf-8');
  const timeline = JSON.parse(raw);
  const project = timelineToChatcut(timeline);

  const outputDir = path.dirname(resolvedOutput);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(resolvedOutput, JSON.stringify(project, null, 2), 'utf-8');
  return project;
}

// CLI Execution entrypoint
if (require.main === module) {
  const args = process.argv.slice(2);
  const inputArg = args[0] || 'public/timeline.json';
  const outputArg = args[1] || 'public/chatcut_project.json';

  try {
    console.log(`[Bridge] Converting timeline -> OpenChatCut project...`);
    console.log(`  Input:  ${inputArg}`);
    console.log(`  Output: ${outputArg}`);

    const project = convertTimelineToChatcutFile(inputArg, outputArg);

    console.log(`[Bridge] Conversion successful!`);
    console.log(`  FPS: ${project.fps}`);
    console.log(`  Total Duration (frames): ${project.totalDurationInFrames}`);
    console.log(`  Tracks: ${project.tracks.length}`);
    project.tracks.forEach(t => {
      console.log(`    - [${t.type}] ${t.id} (${t.clips.length} clips)`);
    });
  } catch (err) {
    console.error(`[Bridge Error] Failed to convert timeline:`, err.message);
    process.exit(1);
  }
}

module.exports = {
  timelineToChatcut,
  convertTimelineToChatcutFile
};
