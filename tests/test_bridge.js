/**
 * tests/test_bridge.js
 * 
 * Comprehensive test suite for the OpenChatCut & Remotion Bridge:
 * 1. timeline_sanitizer with 1-frame gap (snapping)
 * 2. timeline_sanitizer with 2-frame overlap (snapping)
 * 3. timeline_sanitizer with large 10-frame gap (filler insertion)
 * 4. Round-trip conversion: public/timeline.json -> chatcut project -> converted timeline.json
 * 5. Word timestamp shifting on clip movement
 * 6. File-level & CLI conversion verification
 */

'use strict';

const fs = require('fs');
const path = require('path');
const assert = require('assert');

const { sanitizeTimelineGaps, validateSceneContinuity } = require('../scripts/bridge/timeline_sanitizer');
const { timelineToChatcut, convertTimelineToChatcutFile } = require('../scripts/bridge/timeline_to_chatcut');
const { chatcutToTimeline, convertChatcutToTimelineFile, shiftWordTimestamps } = require('../scripts/bridge/chatcut_to_timeline');

let passedTests = 0;
let totalTests = 0;

function runTest(testName, testFn) {
  totalTests++;
  try {
    testFn();
    console.log(`\x1b[32m✔ PASS:\x1b[0m ${testName}`);
    passedTests++;
  } catch (err) {
    console.error(`\x1b[31m✖ FAIL:\x1b[0m ${testName}`);
    console.error(err);
  }
}

console.log('\n======================================================');
console.log('🧪 Starting ai-video-studio Bridge Adapter Test Suite');
console.log('======================================================\n');

// -----------------------------------------------------------------------------
// Test 1: timeline_sanitizer with 1-frame gap
// -----------------------------------------------------------------------------
runTest('Test 1: timeline_sanitizer with 1-frame gap (should snap and eliminate gap)', () => {
  const scenes = [
    {
      id: 'scene_01',
      type: 'MinimalHeadline',
      startFrame: 0,
      durationInFrames: 50,
      audioPath: 'audio/s1.wav',
      text: 'First scene',
      words: [{ text: 'First', startFrame: 5, endFrame: 45 }]
    },
    {
      id: 'scene_02',
      type: 'TweetEmbed',
      startFrame: 51, // 1-frame gap (51 - 50 = 1)
      durationInFrames: 40,
      audioPath: 'audio/s2.wav',
      text: 'Second scene',
      words: [{ text: 'Second', startFrame: 2, endFrame: 35 }]
    }
  ];

  const result = sanitizeTimelineGaps(scenes);

  assert.strictEqual(result.gapFixesCount, 1, 'Expected gapFixesCount to be 1');
  assert.strictEqual(result.sanitizedScenes.length, 2, 'Expected exactly 2 scenes after snap');

  const [s1, s2] = result.sanitizedScenes;
  assert.strictEqual(s1.durationInFrames, 51, 'Expected scene 1 duration to snap from 50 to 51');
  assert.strictEqual(s1.startFrame + s1.durationInFrames, s2.startFrame, 'Scene 1 end must match Scene 2 start');
  assert.strictEqual(result.totalDurationInFrames, 91, 'Total duration should be 51 + 40 = 91');

  const continuity = validateSceneContinuity(result.sanitizedScenes);
  assert.strictEqual(continuity.isValid, true, 'Scene continuity validation must pass');
  assert.strictEqual(continuity.errors.length, 0, 'There should be 0 continuity errors');
});

// -----------------------------------------------------------------------------
// Test 2: timeline_sanitizer with 2-frame overlap
// -----------------------------------------------------------------------------
runTest('Test 2: timeline_sanitizer with 2-frame overlap (should snap without error)', () => {
  const scenes = [
    {
      id: 'scene_01',
      type: 'MinimalHeadline',
      startFrame: 0,
      durationInFrames: 50,
      audioPath: 'audio/s1.wav',
      text: 'First scene',
      words: [{ text: 'First', startFrame: 5, endFrame: 47 }]
    },
    {
      id: 'scene_02',
      type: 'TweetEmbed',
      startFrame: 48, // 2-frame overlap (48 - 50 = -2)
      durationInFrames: 40,
      audioPath: 'audio/s2.wav',
      text: 'Second scene',
      words: [{ text: 'Second', startFrame: 2, endFrame: 35 }]
    }
  ];

  const result = sanitizeTimelineGaps(scenes);

  assert.strictEqual(result.gapFixesCount, 1, 'Expected gapFixesCount to be 1');
  assert.strictEqual(result.sanitizedScenes.length, 2, 'Expected exactly 2 scenes after overlap snap');

  const [s1, s2] = result.sanitizedScenes;
  assert.strictEqual(s1.durationInFrames, 48, 'Expected scene 1 duration to snap from 50 down to 48');
  assert.strictEqual(s1.startFrame + s1.durationInFrames, s2.startFrame, 'Scene 1 end must match Scene 2 start');
  assert.strictEqual(result.totalDurationInFrames, 88, 'Total duration should be 48 + 40 = 88');

  // Verify word endFrame clamping safeguard
  assert.ok(s1.words[0].endFrame <= s1.durationInFrames, 'Word endFrame must not exceed scene duration');

  const continuity = validateSceneContinuity(result.sanitizedScenes);
  assert.strictEqual(continuity.isValid, true, 'Scene continuity validation must pass');
  assert.strictEqual(continuity.errors.length, 0, 'There should be 0 continuity errors');
});

// -----------------------------------------------------------------------------
// Test 3: timeline_sanitizer with large 10-frame gap
// -----------------------------------------------------------------------------
runTest('Test 3: timeline_sanitizer with large 10-frame gap (should insert filler)', () => {
  const scenes = [
    {
      id: 'scene_01',
      type: 'MinimalHeadline',
      startFrame: 0,
      durationInFrames: 50,
      audioPath: 'audio/s1.wav',
      text: 'Scene before gap',
      words: []
    },
    {
      id: 'scene_02',
      type: 'TweetEmbed',
      startFrame: 60, // 10-frame gap (60 - 50 = 10)
      durationInFrames: 40,
      audioPath: 'audio/s2.wav',
      text: 'Scene after gap',
      words: []
    }
  ];

  const result = sanitizeTimelineGaps(scenes);

  assert.strictEqual(result.gapFixesCount, 1, 'Expected gapFixesCount to be 1');
  assert.strictEqual(result.sanitizedScenes.length, 3, 'Expected 3 scenes (original 2 + 1 inserted filler)');

  const [s1, filler, s2] = result.sanitizedScenes;

  assert.strictEqual(filler.isFiller, true, 'Inserted scene must have isFiller = true');
  assert.strictEqual(filler.type, 'Filler', 'Inserted scene must have type = "Filler"');
  assert.strictEqual(filler.startFrame, 50, 'Filler startFrame must be 50');
  assert.strictEqual(filler.durationInFrames, 10, 'Filler durationInFrames must be 10');
  assert.ok(filler.id.startsWith('filler_'), `Filler ID should start with filler_, got: ${filler.id}`);

  // Check continuity across all 3 segments
  assert.strictEqual(s1.startFrame + s1.durationInFrames, filler.startFrame, 'Scene 1 end must equal filler start');
  assert.strictEqual(filler.startFrame + filler.durationInFrames, s2.startFrame, 'Filler end must equal Scene 2 start');
  assert.strictEqual(result.totalDurationInFrames, 100, 'Total duration should be 50 + 10 + 40 = 100');

  const continuity = validateSceneContinuity(result.sanitizedScenes);
  assert.strictEqual(continuity.isValid, true, 'Sanitized scenes must have valid continuous timeline');
  assert.strictEqual(continuity.errors.length, 0, 'There should be 0 continuity errors');
});

// -----------------------------------------------------------------------------
// Test 4: Round-trip conversion: public/timeline.json -> chatcut -> timeline.json
// -----------------------------------------------------------------------------
runTest('Test 4: Round-trip conversion: public/timeline.json -> chatcut -> timeline.json (0 data loss)', () => {
  const originalTimelinePath = path.resolve(__dirname, '../public/timeline.json');
  assert.ok(fs.existsSync(originalTimelinePath), 'public/timeline.json must exist');

  const originalRaw = fs.readFileSync(originalTimelinePath, 'utf-8');
  const originalTimeline = JSON.parse(originalRaw);

  // 1. Convert to OpenChatCut project
  const chatcutProject = timelineToChatcut(originalTimeline);

  // Validate OpenChatCut project structure
  assert.strictEqual(chatcutProject.fps, originalTimeline.fps, 'FPS must match original');
  assert.strictEqual(chatcutProject.totalDurationInFrames, originalTimeline.totalDurationInFrames, 'Total duration must match');
  assert.ok(Array.isArray(chatcutProject.tracks), 'Tracks must be an array');
  assert.strictEqual(chatcutProject.tracks.length, 3, 'Must have exactly 3 tracks');

  const voiceTrack = chatcutProject.tracks.find(t => t.id === 'track-voiceover');
  const brollTrack = chatcutProject.tracks.find(t => t.id === 'track-broll');
  const subTrack = chatcutProject.tracks.find(t => t.id === 'track-subtitles');

  assert.ok(voiceTrack, 'track-voiceover must exist');
  assert.ok(brollTrack, 'track-broll must exist');
  assert.ok(subTrack, 'track-subtitles must exist');

  assert.strictEqual(voiceTrack.clips.length, originalTimeline.scenes.length, 'Voiceover clip count must equal scene count');
  assert.strictEqual(brollTrack.clips.length, originalTimeline.scenes.length, 'B-Roll clip count must equal scene count');
  assert.strictEqual(subTrack.clips.length, originalTimeline.scenes.length, 'Subtitles clip count must equal scene count');

  // Verify voiceover clip schema
  voiceTrack.clips.forEach((clip, idx) => {
    const origScene = originalTimeline.scenes[idx];
    assert.strictEqual(clip.id, origScene.id, `Clip ${idx} id mismatch`);
    assert.strictEqual(clip.startFrame, origScene.startFrame, `Clip ${idx} startFrame mismatch`);
    assert.strictEqual(clip.durationInFrames, origScene.durationInFrames, `Clip ${idx} duration mismatch`);
    assert.strictEqual(clip.source, origScene.audioPath, `Clip ${idx} source mismatch`);
    assert.strictEqual(clip.text, origScene.text, `Clip ${idx} text mismatch`);
    assert.strictEqual(clip.emotion, origScene.emotion, `Clip ${idx} emotion mismatch`);
  });

  // Verify broll clip schema (broll- prefix and sources)
  brollTrack.clips.forEach((clip, idx) => {
    const origScene = originalTimeline.scenes[idx];
    assert.strictEqual(clip.id, `broll-${origScene.id}`, `B-roll clip ${idx} id mismatch`);
    assert.strictEqual(clip.startFrame, origScene.startFrame);
    assert.strictEqual(clip.durationInFrames, origScene.durationInFrames);
    const expectedSource = origScene.brollPath || origScene.heroVideo || origScene.heroImage || `footage/${origScene.id}.mp4`;
    assert.strictEqual(clip.source, expectedSource);
  });

  // Verify subtitles clip schema (sub- prefix)
  subTrack.clips.forEach((clip, idx) => {
    const origScene = originalTimeline.scenes[idx];
    assert.strictEqual(clip.id, `sub-${origScene.id}`, `Sub clip ${idx} id mismatch`);
    assert.strictEqual(clip.startFrame, origScene.startFrame);
    assert.strictEqual(clip.durationInFrames, origScene.durationInFrames);
    assert.strictEqual(clip.text, origScene.text);
  });

  // 2. Convert back from OpenChatCut project to Remotion timeline
  const convertedTimeline = chatcutToTimeline(chatcutProject);

  // Validate converted timeline against original
  assert.strictEqual(convertedTimeline.scenes.length, originalTimeline.scenes.length, 'Scene count must be preserved');
  assert.strictEqual(convertedTimeline.totalDurationInFrames, originalTimeline.totalDurationInFrames, 'Total duration must be preserved');
  assert.strictEqual(convertedTimeline.fps, originalTimeline.fps, 'FPS must be preserved');

  // Detailed per-scene and per-word lossless comparison
  for (let i = 0; i < originalTimeline.scenes.length; i++) {
    const orig = originalTimeline.scenes[i];
    const conv = convertedTimeline.scenes[i];

    assert.strictEqual(conv.id, orig.id, `Scene ${i} ID mismatch`);
    assert.strictEqual(conv.type, orig.type, `Scene ${i} type mismatch`);
    assert.strictEqual(conv.startFrame, orig.startFrame, `Scene ${i} startFrame mismatch`);
    assert.strictEqual(conv.durationInFrames, orig.durationInFrames, `Scene ${i} duration mismatch`);
    assert.strictEqual(conv.audioPath, orig.audioPath, `Scene ${i} audioPath mismatch`);
    assert.strictEqual(conv.text, orig.text, `Scene ${i} text mismatch`);
    assert.strictEqual(conv.emotion, orig.emotion, `Scene ${i} emotion mismatch`);

    // Verify words array
    const origWords = orig.words || [];
    const convWords = conv.words || [];
    assert.strictEqual(convWords.length, origWords.length, `Scene ${i} words count mismatch`);

    for (let w = 0; w < origWords.length; w++) {
      const ow = origWords[w];
      const cw = convWords[w];
      assert.strictEqual(cw.text, ow.text, `Scene ${i} word ${w} text mismatch`);
      assert.strictEqual(cw.startFrame, ow.startFrame, `Scene ${i} word ${w} startFrame mismatch`);
      assert.strictEqual(cw.endFrame, ow.endFrame, `Scene ${i} word ${w} endFrame mismatch`);
      assert.strictEqual(cw.globalStartFrame, ow.globalStartFrame, `Scene ${i} word ${w} globalStartFrame mismatch`);
      assert.strictEqual(cw.globalEndFrame, ow.globalEndFrame, `Scene ${i} word ${w} globalEndFrame mismatch`);
      assert.strictEqual(cw.startMs, ow.startMs, `Scene ${i} word ${w} startMs mismatch`);
      assert.strictEqual(cw.endMs, ow.endMs, `Scene ${i} word ${w} endMs mismatch`);
    }

    // Custom metadata preservation (e.g. tweet, binaryBento, title, etc.)
    if (orig.tweet) {
      assert.deepStrictEqual(conv.tweet, orig.tweet, `Scene ${i} tweet object mismatch`);
    }
    if (orig.binaryBento) {
      assert.deepStrictEqual(conv.binaryBento, orig.binaryBento, `Scene ${i} binaryBento object mismatch`);
    }
    if (orig.title) {
      assert.strictEqual(conv.title, orig.title, `Scene ${i} title mismatch`);
    }
  }

  // Continuity check
  const continuity = validateSceneContinuity(convertedTimeline.scenes);
  assert.strictEqual(continuity.isValid, true, 'Converted timeline must pass continuity check');
});

// -----------------------------------------------------------------------------
// Test 5: Word timestamp shifting on clip movement
// -----------------------------------------------------------------------------
runTest('Test 5: Preserves and shifts word timestamps if clips moved in chatcut', () => {
  const originalClip = {
    id: 'scene_02',
    type: 'TweetEmbed',
    startFrame: 54,
    durationInFrames: 91,
    source: 'audio/scene_02.wav',
    text: 'Tibo 发推表示，第六天只做 Reset。',
    words: [
      {
        text: 'Tibo 发推表示',
        startFrame: 4,
        endFrame: 48,
        globalStartFrame: 58,
        globalEndFrame: 102,
        startMs: 130,
        endMs: 1610
      },
      {
        text: '第六天只做 Reset',
        startFrame: 48,
        endFrame: 84,
        globalStartFrame: 102,
        globalEndFrame: 138,
        startMs: 1610,
        endMs: 2785
      }
    ]
  };

  // User in OpenChatCut moves clip to start at frame 100 instead of 54
  const movedClip = {
    ...originalClip,
    startFrame: 100
  };

  const project = {
    fps: 30,
    totalDurationInFrames: 250,
    tracks: [
      {
        id: 'track-voiceover',
        type: 'audio',
        name: 'Voiceover',
        clips: [
          {
            id: 'scene_01',
            type: 'MinimalHeadline',
            startFrame: 0,
            durationInFrames: 100, // gapless connection with moved clip
            source: 'audio/scene_01.wav',
            text: 'Intro',
            words: []
          },
          movedClip
        ]
      }
    ]
  };

  const timeline = chatcutToTimeline(project);
  const targetScene = timeline.scenes.find(s => s.id === 'scene_02');

  assert.ok(targetScene, 'Scene 02 must exist in converted timeline');
  assert.strictEqual(targetScene.startFrame, 100, 'Scene 02 startFrame must be 100');

  // Verify local startFrame/endFrame are preserved, while global frames are shifted
  assert.strictEqual(targetScene.words[0].startFrame, 4, 'Word 0 local startFrame should remain 4');
  assert.strictEqual(targetScene.words[0].endFrame, 48, 'Word 0 local endFrame should remain 48');
  assert.strictEqual(targetScene.words[0].globalStartFrame, 104, 'Word 0 globalStartFrame should shift to 100 + 4 = 104');
  assert.strictEqual(targetScene.words[0].globalEndFrame, 148, 'Word 0 globalEndFrame should shift to 100 + 48 = 148');
  assert.strictEqual(targetScene.words[0].startMs, 130, 'Word 0 startMs acoustic timestamp must remain intact');
  assert.strictEqual(targetScene.words[0].endMs, 1610, 'Word 0 endMs acoustic timestamp must remain intact');

  assert.strictEqual(targetScene.words[1].startFrame, 48, 'Word 1 local startFrame should remain 48');
  assert.strictEqual(targetScene.words[1].endFrame, 84, 'Word 1 local endFrame should remain 84');
  assert.strictEqual(targetScene.words[1].globalStartFrame, 148, 'Word 1 globalStartFrame should shift to 100 + 48 = 148');
  assert.strictEqual(targetScene.words[1].globalEndFrame, 184, 'Word 1 globalEndFrame should shift to 100 + 84 = 184');
});

// -----------------------------------------------------------------------------
// Test 6: File-level conversion & CLI integration
// -----------------------------------------------------------------------------
runTest('Test 6: File-level converter writes valid JSON and default CLI files', () => {
  const tmpProjectFile = path.resolve(__dirname, '../public/chatcut_project_test_tmp.json');
  const tmpTimelineFile = path.resolve(__dirname, '../public/timeline_test_tmp.json');

  try {
    // Convert public/timeline.json -> tmpProjectFile
    const origTimeline = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../public/timeline.json'), 'utf-8'));
    const project = convertTimelineToChatcutFile('public/timeline.json', tmpProjectFile);
    assert.ok(fs.existsSync(tmpProjectFile), 'chatcut_project_test_tmp.json must be written to disk');

    // Convert tmpProjectFile -> tmpTimelineFile
    const timeline = convertChatcutToTimelineFile(tmpProjectFile, tmpTimelineFile);
    assert.ok(fs.existsSync(tmpTimelineFile), 'timeline_test_tmp.json must be written to disk');

    assert.strictEqual(timeline.scenes.length, origTimeline.scenes.length, 'Converted file must match original scene count');
    assert.strictEqual(timeline.totalDurationInFrames, origTimeline.totalDurationInFrames, 'Converted file must match original total frames');
  } finally {
    // Cleanup temporary test files
    if (fs.existsSync(tmpProjectFile)) fs.unlinkSync(tmpProjectFile);
    if (fs.existsSync(tmpTimelineFile)) fs.unlinkSync(tmpTimelineFile);
  }
});

console.log('\n======================================================');
console.log(`Results: ${passedTests}/${totalTests} tests passed (${Math.round((passedTests / totalTests) * 100)}%)`);
console.log('======================================================\n');

if (passedTests !== totalTests) {
  process.exit(1);
} else {
  process.exit(0);
}
