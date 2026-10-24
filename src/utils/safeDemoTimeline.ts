/**
 * src/utils/safeDemoTimeline.ts
 * 运行时安全加载 public/projects 下的 demo timeline (Phase 0 A1 补齐)
 *
 * 背景: public/projects/ 被 .gitignore 忽略 (本地产物目录), 三个 demo 视图
 * (AppleKeynoteView / FireshipKineticView / MotionCanvasView) 曾静态 import
 * 其中的 timeline.json, 导致干净检出 (CI / 新同事 clone) 下 tsc --noEmit 直接
 * 失败 (TS2307 Cannot find module) —— 该缺陷自 Phase 0 起潜伏, 由 CI 首次曝光。
 *
 * 本模块以 webpack require.context 在编译期收集、运行时按需加载, 缺失时降级为
 * 空时间轴, 保障:
 *   1. 源码零静态 JSON import -> 干净检出编译通过;
 *   2. webpack (Remotion) 构建中文件存在则注入真实数据, 不存在则降级不崩;
 *   3. 纯 Node 测试环境 (无 require.context) 同样降级, 不抛错。
 */

export interface DemoTimeline {
  scenes: Array<Record<string, any>>;
  totalDurationInFrames?: number;
  theme?: string;
  [key: string]: any;
}

const EMPTY_TIMELINE: DemoTimeline = { scenes: [], totalDurationInFrames: 0 };

// webpack require.context 的局部声明 (不依赖 @types/node 全局注入, 避免影响根 tsconfig)
declare const require: ((id: string) => any) & {
  context?: (path: string, deep?: boolean, filter?: RegExp) => (p: string) => any;
};

function createDemoContext(): ((p: string) => any) | null {
  try {
    if (typeof require !== 'function' || typeof require.context !== 'function') {
      return null; // 非 webpack 环境 (Node 测试/SSR)
    }
    // 编译期收集 public/projects 下全部 timeline.json (递归)
    return require.context('../../../public/projects', true, /timeline\.json$/);
  } catch {
    return null;
  }
}

const demoContext = createDemoContext();

/**
 * 安全加载 demo timeline; 文件缺失或结构不符时降级为空时间轴 ( scenes: [] ),
 * 调用方需对 scenes[0] 做防御性访问 (见各 demo 视图的 `|| { words: [] }`)。
 */
export function safeLoadDemoTimeline(projectDir: string): DemoTimeline {
  if (!demoContext) {
    return { ...EMPTY_TIMELINE };
  }
  try {
    const data = demoContext(`./${projectDir}/timeline.json`);
    if (data && typeof data === 'object' && Array.isArray(data.scenes)) {
      return data as DemoTimeline;
    }
    return { ...EMPTY_TIMELINE };
  } catch {
    // 干净检出未生成该文件: 降级空时间轴, demo 组合渲染空场景而非编译失败
    return { ...EMPTY_TIMELINE };
  }
}
