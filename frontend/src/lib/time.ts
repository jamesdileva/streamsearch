// "How long ago was this verified?" — restrained relative age.
export function formatAge(verifiedAt: string, nowMs = Date.now()): string {
  const ageSec = Math.max(0, Math.floor((nowMs - Date.parse(verifiedAt)) / 1000));
  if (ageSec < 60) return 'just now';
  const minutes = Math.floor(ageSec / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}
