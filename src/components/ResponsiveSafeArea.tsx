import React, { createContext, useContext } from 'react';
import { useVideoConfig, AbsoluteFill } from 'remotion';

export interface SafeAreaInsets {
  top: number;
  bottom: number;
  left: number;
  right: number;
  contentWidth: number;
  contentHeight: number;
}

export interface ResponsiveLayoutContextType {
  isVertical: boolean;
  isPortrait: boolean;
  width: number;
  height: number;
  insets: SafeAreaInsets;
  fontScale: number;
  contentFlexDirection: 'row' | 'column';
}

const ResponsiveLayoutContext = createContext<ResponsiveLayoutContextType>({
  isVertical: false,
  isPortrait: false,
  width: 1920,
  height: 1080,
  insets: {
    top: 40,
    bottom: 80,
    left: 60,
    right: 60,
    contentWidth: 1800,
    contentHeight: 960,
  },
  fontScale: 1.0,
  contentFlexDirection: 'row',
});

export const useResponsiveSafeArea = (): ResponsiveLayoutContextType => {
  return useContext(ResponsiveLayoutContext);
};

export const ResponsiveSafeAreaProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { width, height } = useVideoConfig();
  const isVertical = height > width;

  const insets: SafeAreaInsets = isVertical
    ? {
        // 9:16 Vertical Mobile Safe Area (TikTok, Reels, Shorts UI Protection)
        top: 140, // Avoid notch and live badge
        bottom: 280, // Avoid bottom caption and music ticker
        left: 48,
        right: 120, // Avoid vertical interaction column (Like, Comment, Share)
        contentWidth: width - 48 - 120,
        contentHeight: height - 140 - 280,
      }
    : {
        // 16:9 Horizontal Desktop / YouTube Safe Area
        top: 50,
        bottom: 90, // Avoid progress bar and player controls
        left: 80,
        right: 80,
        contentWidth: width - 160,
        contentHeight: height - 140,
      };

  const fontScale = isVertical ? 0.85 : 1.0;
  const contentFlexDirection: 'row' | 'column' = isVertical ? 'column' : 'row';

  const contextValue: ResponsiveLayoutContextType = {
    isVertical,
    isPortrait: isVertical,
    width,
    height,
    insets,
    fontScale,
    contentFlexDirection,
  };

  return (
    <ResponsiveLayoutContext.Provider value={contextValue}>
      {children}
    </ResponsiveLayoutContext.Provider>
  );
};

export const ResponsiveSafeArea: React.FC<{
  children: React.ReactNode;
  style?: React.CSSProperties;
  enableDebugGuides?: boolean;
}> = ({ children, style, enableDebugGuides = false }) => {
  return (
    <ResponsiveSafeAreaProvider>
      <ResponsiveSafeAreaContent style={style} enableDebugGuides={enableDebugGuides}>
        {children}
      </ResponsiveSafeAreaContent>
    </ResponsiveSafeAreaProvider>
  );
};

const ResponsiveSafeAreaContent: React.FC<{
  children: React.ReactNode;
  style?: React.CSSProperties;
  enableDebugGuides?: boolean;
}> = ({ children, style, enableDebugGuides }) => {
  const { insets, isVertical } = useResponsiveSafeArea();

  return (
    <AbsoluteFill
      style={{
        boxSizing: 'border-box',
        paddingTop: insets.top,
        paddingBottom: insets.bottom,
        paddingLeft: insets.left,
        paddingRight: insets.right,
        display: 'flex',
        flexDirection: isVertical ? 'column' : 'row',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        ...style,
      }}
    >
      {enableDebugGuides && (
        <AbsoluteFill
          style={{
            pointerEvents: 'none',
            border: isVertical ? '2px dashed rgba(244, 63, 94, 0.4)' : '2px dashed rgba(56, 189, 248, 0.4)',
            boxSizing: 'border-box',
            margin: `${insets.top}px ${insets.right}px ${insets.bottom}px ${insets.left}px`,
          }}
        />
      )}
      {children}
    </AbsoluteFill>
  );
};
