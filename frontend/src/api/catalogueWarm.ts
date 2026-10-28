import { api } from "./client";
import { getPyqCatalogue } from "./pyq";
import { resources } from "@/src/resourceCache";

/** Navigation intent gets priority over the one-lane speculative RF prefetch. */
export function warmExamCatalogue(uid: string, slug: string) {
  if (!uid) return;
  if (slug === "jee-main") {
    void resources.request(`u.${uid}.pyq.jee-main`, getPyqCatalogue, false).catch(() => {});
  } else if (slug === "bitsat" || slug === "comedk") {
    const path = `/exam-navigation/${slug}/catalogue?${new URLSearchParams({ kind: "mocks", subject: "", q: "", page: "1" })}`;
    void resources.request(`u.${uid}.${path}`, signal => api(path, { signal }), false).catch(() => {});
  }
}