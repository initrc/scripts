#!/usr/bin/env bash

# Try Wi-Fi first, then common wired interfaces.
for interface in en0 en1 en2; do
  ip=$(ipconfig getifaddr "$interface" 2>/dev/null)

  if [[ -n "$ip" ]]; then
    echo "Local IP on $interface: $ip"
    exit 0
  fi
done

echo "No local IP address found on en0, en1, or en2."
exit 1

