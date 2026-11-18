# Server size request for jeelive.ai (ready to send to platform support)

Send to: support@emergent.sh (or the in-app support chat), from the owner's account.

---

Subject: Capacity increase for jeelive.ai before a 1 lakh student live exam

Hello,

My app jeelive.ai will hold a live JEE exam for 20,000 to 1,00,000 students at the same time (3-hour paper, everyone starts within about 15 minutes). I need the production setup sized for 1 lakh students before that date.

What the app measured (staged load test on the preview setup, 18 Nov 2026, docs/CAPACITY_REPORT_2026-11-18.md):
- Each student uses about 1.2 backend CPU-seconds and 0.43 database CPU-seconds over a 3-hour paper (sign-in, start, the whole paper's pictures, about 150 answer saves with time records, about 75 visits, submit, grading, results, analysis).
- One preview server (2 vCPU, one process, database on the same machine) handled 1,000 students joining within 30 seconds with zero failed saves; 2,000 saturated it.
- 1 lakh: about 11 vCPU backend on average and about 45 vCPU during the 15-minute start (question pictures, about 7.4 MB per student, about 740 GB in total). 2 lakh: about 22 vCPU on average and about 90 vCPU at the start.
- From one IP, Cloudflare started answering "Just a moment…" (429) at about 500 students. School and coaching Wi-Fi users would be blocked the same way.
- Today production (tier_4 Elite) runs 2 pods, each with 2 vCPU requested and a 4 vCPU limit (8 Gi / 16 Gi memory).

What I am asking for:
1. Backend: about 24 workers (for example 6 pods x 4 vCPU with 4 workers each) for 1 lakh, about 48 for 2 lakh, for the exam window. Please tell me how many app workers run in each pod today, because one Python worker uses at most about 1 core.
2. Database: a MongoDB tier with about 8 vCPU (1 lakh) or 16 vCPU (2 lakh) that sustains about 1,400 (2,800) answer writes per second for 3 hours, and about 7 GB (14 GB) of new data per paper. Please also tell me the current database size, whether backups are taken and when the last one ran, and whether any slow queries are logged.
2b. Cloudflare: please do not challenge or rate-limit jeelive.ai /api calls from shared IPs (school/coaching Wi-Fi, mobile carrier NAT) during exams.
3. Sign-in rush: about 1,300 sign-ins per minute for 15 minutes before the start (20,000 students), up to about 6,700 per minute for 1 lakh.
4. The 30-second hangs (Cloudflare 520) seen earlier on jeelive.ai: please check the edge to pod path and Cloudflare analytics (earlier RCA 402afcbe-cbe8-4eb7-aa1b-491fa5beb602). The app's own logs do not record request times, so these can only be seen from the edge.
5. After the increase, permission to run one staged load test at exam size on that setup, a few days before the exam.

Please tell me the cost, how soon it can be ready, and whether autoscaling is possible so I only pay for the larger size during exams.

Thank you,
[Owner name]
jeelive.ai
