#!/bin/sh
# Native dependency for the confined Office renderer; no environment secrets required.
set -eu
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends libreoffice-writer libreoffice-calc libseccomp2
