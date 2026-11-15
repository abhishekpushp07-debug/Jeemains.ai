import { api } from "./client";
import { getPyqCatalogue } from "./pyq";
import { cataloguePath } from "./examCatalog";
import { resources } from "@/src/resourceCache";

/** Navigation intent gets priority over the one-lane speculative RF prefetch. */
export function warmExamCatalogue(uid: string, slug: string) {
  if (!uid || !slug) return;
  if (slug === "jee-main") {
    void resources.request(`u.${uid}.pyq.jee-main`, getPyqCatalogue, false).catch(() => {});
  } else {
    const path = cataloguePath(slug, "mocks", "", "", "", 1);
    void resources.request(`u.${uid}.${path}`, signal => api(path, { signal }), false).catch(() => {});
  }
}
