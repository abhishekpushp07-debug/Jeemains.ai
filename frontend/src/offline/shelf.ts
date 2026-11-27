// Big text kept on the phone itself (Rapid Fire's cards are about 7 MB): plain files, because AsyncStorage is for
// small values. Nothing personal is written here. Every call answers quietly (null / false) when the phone refuses,
// and the app then simply works as it does without a kept copy.
import { Directory, File, Paths } from "expo-file-system";

const root = () => new Directory(Paths.document, "jeelive-kept-v1");
const valid = (name: string) => /^[a-z0-9][a-z0-9._-]{0,79}$/i.test(name);

export const shelf = {
  async read(name: string): Promise<string | null> {
    try {
      if (!valid(name)) return null;
      const file = new File(root(), name);
      return file.exists ? await file.text() : null;
    } catch { return null; }
  },
  /** Written beside the old copy first and moved over it, so a half-written file is never read. */
  async write(name: string, text: string): Promise<boolean> {
    try {
      if (!valid(name)) return false;
      await root().create({ intermediates: true, idempotent: true });
      const temp = new File(root(), `${name}.tmp`);
      await temp.write(text);
      await temp.move(new File(root(), name), { overwrite: true });
      return true;
    } catch { return false; }
  },
  async remove(name: string): Promise<void> {
    try { const file = new File(root(), name); if (valid(name) && file.exists) await file.delete(); } catch { /* nothing to remove */ }
  },
};
