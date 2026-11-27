// A browser has no background run of its own: the web preview and the browser Rapid Fire keep things only while the
// page is open (./door.tsx). The phone's version: ./background.ts.
export async function scheduleKeeping(_on: boolean): Promise<void> {}
