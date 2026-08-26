#!/usr/bin/env python3
"""Scheduled Background Runner for 19 August 2026 09:30 Europe/Istanbul."""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

def main():
    target_tz = ZoneInfo("Europe/Istanbul")
    target_time = datetime(2026, 8, 19, 9, 30, 0, tzinfo=target_tz)
    
    print(f"⏰ Scheduled Runner Active!")
    print(f"Target Execution Time: {target_time.isoformat()}")
    
    while True:
        now = datetime.now(target_tz)
        remaining_sec = (target_time - now).total_seconds()
        
        if remaining_sec <= 0:
            print(f"\n🚀 Target time reached ({now.isoformat()})! Launching Wave 3 campaign send...\n")
            os.system("PYTHONPATH=. python3 scripts/send_wave3.py")
            break
            
        print(f"[{now.strftime('%H:%M:%S')}] Waiting... Remaining: {int(remaining_sec)} seconds (~{int(remaining_sec/60)} mins)")
        sleep_sec = min(remaining_sec, 300) # sleep max 5 mins per tick
        time.sleep(sleep_sec)

if __name__ == "__main__":
    main()
