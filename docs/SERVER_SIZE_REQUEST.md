# Server size request for jeelive.ai (ready to send to platform support)

Send to: support@emergent.sh (or the in-app support chat), from the owner's account.

---

Subject: Capacity increase for jeelive.ai before a 1 lakh student live exam

Hello,

My app jeelive.ai will hold a live JEE exam for 20,000 to 1,00,000 students at the same time (3-hour paper, everyone starts within about 15 minutes). I need the production setup sized for 1 lakh students before that date.

What the app measured (not a new load test; earlier measurements on the preview setup):
- Each student uses about 0.9 to 1.25 CPU-seconds over a 3-hour paper (sign-in, start, about 150 answer saves, about 75 question visits, submit, grading, results).
- Today production runs on 2 pods with a 1 vCPU limit each. That holds about 10,000 exam starts per minute and roughly 16,000 to 22,000 students writing at the same time.

What I am asking for:
1. Backend: 10 to 12 vCPU in total for the exam window (for example 6 pods x 2 vCPU, or autoscaling from 2 up to 12 pods), memory as today per pod (4 GiB limit is enough).
2. Database: a MongoDB tier that sustains about 1,400 answer writes per second for 3 hours, with backups and a tested restore.
3. Sign-in rush: about 1,300 sign-ins per minute for 15 minutes before the start (20,000 students), up to about 6,700 per minute for 1 lakh.
4. The 30-second hangs (Cloudflare 520) seen earlier on jeelive.ai: please check the edge to pod path (earlier RCA 402afcbe-cbe8-4eb7-aa1b-491fa5beb602).
5. After the increase, permission to run one staged load test at exam size on that setup, a few days before the exam.

Please tell me the cost, how soon it can be ready, and whether autoscaling is possible so I only pay for the larger size during exams.

Thank you,
[Owner name]
jeelive.ai
