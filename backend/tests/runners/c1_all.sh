#!/bin/bash
# TEST-ONLY pocket C1a: the browser walk first, then the long suites, strictly one after another (never two disposable databases at work together).
bash /root/p2/links_ui.sh
bash /root/p2/c1_chain.sh full251 aits_a build253 unit252 iso254
