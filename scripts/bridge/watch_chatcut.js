/**
 * scripts/bridge/watch_chatcut.js
 * 
 * OpenChatCut <-> Remotion Hot-Reloading Watcher Daemon
 * Monitors project.json changes in real time and automatically runs
 * bridge sync and timeline gap sanitization without manual intervention.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { chatcutToTimeline } = require('./chatcut_to_timeline');
const { sanitizeTimelineGaps, validateSceneContinuity } = require('./timeline_sanitizer');

const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const PRIMARY_CHATCUT_PATH = path.join(PROJECT_ROOT, 'projects_chatcut', 'default_project', 'project.json');
const FALLBACK_CHATCUT_PATH = path.join(PROJECT_ROOT, 'public', 'chatcut_project.json');
const DEFAULT_CHATCUT_PROJECT = fs.existsSync(PRIMARY_CHATCUT_PATH) ? PRIMARY_CHATCUT_PATH : FALLBACK_CHATCUT_PATH;
const DEFAULT_TIMELINE = path.join(PROJECT_ROOT, 'inputs', 'timeline.json');

/**
 * Executes a single synchronization cycle from OpenChatCut to Remotion timeline.json.
 * 
 * @param {string} chatcutPath 
 * @param {string} timelinePath 
 * @returns {{ success: boolean, gapFixesCount: number, sceneCount: number }}
 */
function syncOnce(chatcutPath = DEFAULT_CHATCUT_PROJECT, timelinePath = DEFAULT_TIMELINE) {
  if (!fs.existsSync(chatcutPath)) {
    console.error(`[OpenChatCut Watcher] ❌ Project file does not exist: ${chatcutPath}`);
    return { success: false, gapFixesCount: 0, sceneCount: 0 };
  }

  try {
    const rawData = fs.readFileSync(chatcutPath, 'utf-8');
    const projectJson = JSON.parse(rawData);

    // Convert to Remotion timeline schema
    const converted = chatcutToTimeline(projectJson);
    const sanitized = sanitizeTimelineGaps(converted.scenes);

    const resultTimeline = {
      ...converted,
      scenes: sanitized.sanitizedScenes,
      totalDurationInFrames: sanitized.totalDurationInFrames,
      lastSyncedAt: new Date().toISOString()
    };

    const outDir = path.dirname(timelinePath);
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    fs.writeFileSync(timelinePath, JSON.stringify(resultTimeline, null, 2), 'utf-8');

    const timestamp = new Date().toLocaleTimeString();
    console.log(
      `[OpenChatCut Watcher] [${timestamp}] 🔄 Auto-synced ${resultTimeline.scenes.length} scenes -> ${path.basename(timelinePath)} (Sanitized gaps: ${sanitized.gapFixesCount}, valid: ${sanitized.isValid})`
    );

    return {
      success: true,
      gapFixesCount: sanitized.gapFixesCount,
      sceneCount: resultTimeline.scenes.length
    };
  } catch (err) {
    console.error(`[OpenChatCut Watcher] ❌ Sync error:`, err.message);
    return { success: false, gapFixesCount: 0, sceneCount: 0, error: err.message };
  }
}

/**
 * Starts continuous file watching with debounce.
 */
function startWatching(chatcutPath = DEFAULT_CHATCUT_PROJECT, timelinePath = DEFAULT_TIMELINE) {
  const targetDir = path.dirname(chatcutPath);
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }

  // Initial sync on startup
  if (fs.existsSync(chatcutPath)) {
    console.log(`[OpenChatCut Watcher] 🚀 Initializing sync on startup...`);
    syncOnce(chatcutPath, timelinePath);
  }

  console.log(`[OpenChatCut Watcher] 👁️  Watching for OpenChatCut changes in: ${chatcutPath}`);
  console.log(`[OpenChatCut Watcher] 💡 Saves in OpenChatCut will instantly update ${timelinePath}`);

  let debounceTimer = null;
  const targetBasename = path.basename(chatcutPath);

  fs.watch(targetDir, (eventType, filename) => {
    if (filename && filename.toLowerCase() === targetBasename.toLowerCase()) {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
      debounceTimer = setTimeout(() => {
        syncOnce(chatcutPath, timelinePath);
      }, 300);
    }
  });
}

// CLI handler
if (require.main === module) {
  const args = process.argv.slice(2);
  const isOnce = args.includes('--once');
  const customProject = args.find(a => !a.startsWith('--') && a.endsWith('.json'));

  const chatcutFile = customProject || DEFAULT_CHATCUT_PROJECT;

  if (isOnce) {
    const res = syncOnce(chatcutFile);
    process.exit(res.success ? 0 : 1);
  } else {
    startWatching(chatcutFile);
  }
}

module.exports = {
  syncOnce,
  startWatching
};
