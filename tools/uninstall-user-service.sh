#!/usr/bin/env bash
set -euo pipefail

SERVICE_FILE="${HOME}/.config/systemd/user/personal-cic.service"

systemctl --user disable --now personal-cic.service 2>/dev/null || true
rm -f "${SERVICE_FILE}"
systemctl --user daemon-reload

echo "Personal CIC user service removed."
