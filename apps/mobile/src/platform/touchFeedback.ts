export function createAndroidRipple(color: string, borderless = false) {
  return { borderless, color, foreground: true } as const;
}
