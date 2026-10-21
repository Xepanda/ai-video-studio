/**
 * scripts/bridge/watch_chatcut.js
 *
 * OpenChatCut <-> Remotion Hot-Reloading Watcher Daemon
 * Monitors project.json changes in real time and automatically runs
 * bridge sync and timeline gap sanitization without manual intervention.
 *
 * 输出目标 (审计 A2 修复): 默认写入 public/timeline.json —— Remotion
 * (src/Root.tsx 静态导入 + UniversalScene) 的实际消费路径;
 * 旧版写入 inputs/timeline.json 无任何消费方, "保存即刷新"链路断裂。
 * 可用 --timeline <path> 覆盖 (例如 public/projects/<project>/timeline.json)。
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
// Remotion 渲染层真实消费路径 (原 inputs/timeline.json 无消费方, 链路断裂)
const DEFAULT_TIMELINE = path.join(PROJECT_ROOT, 'public', 'timeline.json');

/**
 * 原子化写入 JSON: 先写临时文件再 rename, 避免 Remotion HMR 读到半个文件。
 * @param {string} targetPath
 * @param {any} data
 */
function atomicWriteJson(targetPath, data) {
  const outDir = path.dirname(targetPath);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }
  const tmpPath = `${targetPath}.tmp-${process.pid}-${Date.now()}`;
  fs.writeFileSync(tmpPath, JSON.stringify(data, null, 2), 'utf-8');
  fs.renameSync(tmpPath, targetPath);
}

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

    atomicWriteJson(timelinePath, resultTimeline);

    const timestamp = new Date().toLocaleTimeString();
    console.log(
      `[OpenChatCut Watcher] [${timestamp}] 🔄 Auto-synced ${resultTimeline.scenes.length} scenes -> ${path.relative(PROJECT_ROOT, timelinePath)} (Sanitized gaps: ${sanitized.gapFixesCount}, valid: ${sanitized.isValid})`
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
  console.log(`[OpenChatCut Watcher] 💡 Saves in OpenChatCut will instantly update ${path.relative(PROJECT_ROOT, timelinePath)}`);

  let debounceTimer = null;
  let closed = false;
  const targetBasename = path.basename(chatcutPath);

  let watcher;
  try {
    watcher = fs.watch(targetDir, (eventType, filename) => {
      if (filename && filename.toLowerCase() === targetBasename.toLowerCase()) {
        if (debounceTimer) {
          clearTimeout(debounceTimer);
        }
        debounceTimer = setTimeout(() => {
          syncOnce(chatcutPath, timelinePath);
        }, 300);
      }
    });
  } catch (err) {
    console.error(`[OpenChatCut Watcher] ❌ Failed to start watcher on ${targetDir}:`, err.message);
    process.exit(1);
    return;
  }

  // 文件系统监视错误 (如目录被删除/权限变更) 必须显式处理, 否则进程可能静默失效或崩溃
  watcher.on('error', (err) => {
    console.error(`[OpenChatCut Watcher] ⚠️ Watcher error:`, err.message);
    if (!closed) {
      closed = true;
      try { watcher.close(); } catch { /* 忽略关闭异常 */ }
      console.log(`[OpenChatCut Watcher] 🔁 Attempting to restart watcher in 2s...`);
      setTimeout(() => startWatching(chatcutPath, timelinePath), 2000);
    }
  });

  // 优雅退出: 清理 debounce 定时器与 watcher
  const shutdown = () => {
    closed = true;
    if (debounceTimer) clearTimeout(debounceTimer);
    try { watcher.close(); } catch { /* 忽略关闭异常 */ }
    process.exit(0);
  };
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

// CLI handler
if (require.main === module) {
  const args = process.argv.slice(2);
  const isOnce = args.includes('--once');
  const timelineIdx = args.indexOf('--timeline');
  const customTimeline = timelineIdx !== -1 ? args[timelineIdx + 1] : null;
  // 位置参数仅取 .json 工程文件; 必须排除 --timeline 的取值, 否则会被误判为工程路径
  const positional = args.filter((a, i) => {
    if (a.startsWith('--')) return false;
    if (timelineIdx !== -1 && i === timelineIdx + 1) return false;
    return a.endsWith('.json');
  });
  const customProject = positional[0] || null;

  const chatcutFile = customProject || DEFAULT_CHATCUT_PROJECT;
  const timelineFile = customTimeline || DEFAULT_TIMELINE;

  if (isOnce) {
    const res = syncOnce(chatcutFile, timelineFile);
    process.exit(res.success ? 0 : 1);
  } else {
    startWatching(chatcutFile, timelineFile);
  }
}

module.exports = {
  syncOnce,
  startWatching,
  DEFAULT_TIMELINE,
  DEFAULT_CHATCUT_PROJECT
};
