export interface ThemeColors {
  background: string;
  surface: string;
  surfaceElevated: string;
  surfacePressed: string;
  surfaceDisabled: string;
  foreground: string;
  foregroundMuted: string;
  foregroundSubtle: string;
  foregroundDisabled: string;
  onAction: string;
  accent: string;
  action: string;
  actionPressed: string;
  border: string;
  borderStrong: string;
  focus: string;
  overlay: string;
  success: string;
  successSurface: string;
  warning: string;
  warningSurface: string;
  error: string;
  errorSurface: string;
  danger: string;
  dangerPressed: string;
  info: string;
  infoSurface: string;
}

export const DARK_COLORS: Readonly<ThemeColors> = {
  background: "#171A21",
  surface: "#1B2838",
  surfaceElevated: "#2A475E",
  surfacePressed: "#365E7A",
  surfaceDisabled: "#273441",
  foreground: "#C7D5E0",
  foregroundMuted: "#A7B8C6",
  foregroundSubtle: "#91A6B5",
  foregroundDisabled: "#7F919F",
  onAction: "#FFFFFF",
  accent: "#66C0F4",
  action: "#2A5F7E",
  actionPressed: "#214B64",
  border: "#36566F",
  borderStrong: "#66C0F4",
  focus: "#8BD4FF",
  overlay: "rgba(5, 10, 16, 0.78)",
  success: "#79D49B",
  successSurface: "#183828",
  warning: "#F2C166",
  warningSurface: "#493617",
  error: "#FF9A91",
  errorSurface: "#4B2328",
  danger: "#A63D4D",
  dangerPressed: "#7F2E3A",
  info: "#77C8F5",
  infoSurface: "#17384D",
};

export const LIGHT_COLORS: Readonly<ThemeColors> = {
  background: "#F2F5F7",
  surface: "#FFFFFF",
  surfaceElevated: "#E4EDF2",
  surfacePressed: "#D4E4EC",
  surfaceDisabled: "#E8ECEF",
  foreground: "#1B2838",
  foregroundMuted: "#425466",
  foregroundSubtle: "#526576",
  foregroundDisabled: "#6D7D88",
  onAction: "#FFFFFF",
  accent: "#66C0F4",
  action: "#1B4F6B",
  actionPressed: "#12384D",
  border: "#AAB9C4",
  borderStrong: "#2A475E",
  focus: "#155F86",
  overlay: "rgba(11, 26, 36, 0.58)",
  success: "#17613A",
  successSurface: "#DCF2E5",
  warning: "#754800",
  warningSurface: "#FFF0CC",
  error: "#962C3C",
  errorSurface: "#FCE2E6",
  danger: "#962C3C",
  dangerPressed: "#70202D",
  info: "#155879",
  infoSurface: "#DCEEF7",
};
