import React from 'react';
import { useSafeFrameConfig } from './shorts/useSafeFrameConfig';

/**
 * 单片机/硬件引脚正弦波流光动效 (Pinout Stream)
 * W7-8 数据驱动化: 引脚列表与标题经 props 注入 (分镜 pinoutStream 嵌套配置),
 * 无 props 时回退内置演示数据 (保持 Root.tsx 既有零配置用法兼容)。
 */
export interface PinoutPin {
  /** 引脚名称 (例如 "GPIO 18 (SCLK)") */
  pin: string;
  /** 流光速度系数 (越大越快) */
  freq: number;
  /** 流光颜色 */
  color: string;
}

export interface PinoutStreamProps {
  pins?: PinoutPin[];
  title?: string;
}

const DEFAULT_PINS: PinoutPin[] = [
  { pin: "GPIO 18 (SCLK)", freq: 0.15, color: "#38bdf8" },
  { pin: "GPIO 23 (MOSI)", freq: 0.22, color: "#10b981" },
  { pin: "GPIO 05 (CS)",   freq: 0.08, color: "#f59e0b" },
];

export const PinoutStream: React.FC<PinoutStreamProps> = ({
  pins = DEFAULT_PINS,
  title = "⚡ GPIO 脉冲走线信号波形 (ESP32-S3)",
}) => {
  const { frame } = useSafeFrameConfig();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', width: '100%', padding: '16px', backgroundColor: '#0f172a', borderRadius: '16px', border: '1px solid #1e293b' }}>
      <div style={{ color: '#38bdf8', fontSize: '16px', fontWeight: 700, marginBottom: '4px' }}>
        {title}
      </div>
      {pins.map((item, idx) => {
        return (
          <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span style={{ width: '130px', color: '#94a3b8', fontSize: '14px', fontFamily: 'monospace' }}>{item.pin}</span>
            <div style={{ flex: 1, height: '28px', backgroundColor: '#020617', borderRadius: '6px', overflow: 'hidden', position: 'relative', display: 'flex', alignItems: 'center' }}>
              {/* 正弦波流光点阵 */}
              <div
                style={{
                  position: 'absolute',
                  left: `${(frame * 6 + idx * 40) % 100}%`,
                  width: '60px',
                  height: '100%',
                  background: `linear-gradient(90deg, transparent, ${item.color}, transparent)`,
                  boxShadow: `0 0 15px ${item.color}`,
                }}
              />
              <div style={{ width: '100%', height: '1px', backgroundColor: '#334155' }} />
            </div>
          </div>
        );
      })}
    </div>
  );
};
