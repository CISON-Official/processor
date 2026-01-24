#!/usr/bin/env python3
"""
Celery Worker Manager
Helps manage Celery workers - stop, start, restart, status
"""

import os
import sys
import signal
import subprocess
import time
from pathlib import Path


class CeleryManager:
    def __init__(self, app_name, project_dir=None):
        self.app_name = app_name
        self.project_dir = project_dir or os.getcwd()

    def get_celery_processes(self):
        """Get all running Celery worker processes"""
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)

            processes = []
            for line in result.stdout.split("\n"):
                if f"{self.app_name} worker" in line and "grep" not in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        processes.append(
                            {"pid": int(parts[1]), "command": " ".join(parts[10:])}
                        )

            return processes
        except Exception as e:
            print(f"Error getting processes: {e}")
            return []

    def stop_all(self, force=False):
        """Stop all Celery workers"""
        processes = self.get_celery_processes()

        if not processes:
            print("✓ No Celery workers running")
            return True

        print(f"Found {len(processes)} Celery worker(s) running")

        for proc in processes:
            print(f"  Stopping PID {proc['pid']}...")
            try:
                sig = signal.SIGKILL if force else signal.SIGTERM
                os.kill(proc["pid"], sig)
                print(
                    f"    ✓ Sent {'SIGKILL' if force else 'SIGTERM'} to {proc['pid']}"
                )
            except ProcessLookupError:
                print(f"    ⚠ Process {proc['pid']} already gone")
            except PermissionError:
                print(f"    ✗ Permission denied for PID {proc['pid']}")
                return False

        # Wait for processes to stop
        time.sleep(2)

        # Verify all stopped
        remaining = self.get_celery_processes()
        if remaining:
            print(f"\n⚠ {len(remaining)} process(es) still running")
            if not force:
                print("  Use 'force-stop' to kill forcefully")
                return False
        else:
            print("\n✓ All Celery workers stopped")

        # Clean up PID files
        self.cleanup_pid_files()

        return True

    def cleanup_pid_files(self):
        """Remove stale PID files"""
        pid_files = list(Path(self.project_dir).rglob("*.pid"))

        if pid_files:
            print(f"\nCleaning up {len(pid_files)} PID file(s)...")
            for pid_file in pid_files:
                try:
                    pid_file.unlink()
                    print(f"  ✓ Removed {pid_file}")
                except Exception as e:
                    print(f"  ✗ Failed to remove {pid_file}: {e}")

    def start(self, log_level="info", concurrency=None, queues=None):
        """Start Celery worker"""
        # First check if any workers are running
        if self.get_celery_processes():
            print("✗ Celery workers already running!")
            print("  Run 'stop' first, or use 'restart'")
            return False

        print(f"Starting Celery worker for '{self.app_name}'...")

        # Build command
        cmd = ["uv", "run", "celery", "-A", self.app_name, "worker", "-l", log_level, '--pool=prefork']

        if concurrency:
            cmd.extend(["--concurrency", str(concurrency)])

        if queues:
            cmd.extend(["-Q", queues])

        print(f"Command: {' '.join(cmd)}")

        try:
            # Start in background
            subprocess.Popen(
                cmd,
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait a bit and check if it started
            time.sleep(3)

            if self.get_celery_processes():
                print("✓ Celery worker started successfully")
                return True
            else:
                print("✗ Failed to start Celery worker")
                return False

        except Exception as e:
            print(f"✗ Error starting Celery: {e}")
            return False

    def restart(self, **kwargs):
        """Restart Celery workers"""
        print("Restarting Celery workers...\n")

        # Stop
        if not self.stop_all():
            print("\nForce stopping...")
            if not self.stop_all(force=True):
                print("✗ Failed to stop workers")
                return False

        time.sleep(1)

        # Start
        return self.start(**kwargs)

    def status(self):
        """Show status of Celery workers"""
        processes = self.get_celery_processes()

        print("\n" + "=" * 60)
        print("CELERY WORKER STATUS")
        print("=" * 60)

        if not processes:
            print("No Celery workers running")
        else:
            print(f"Found {len(processes)} worker(s) running:\n")
            for i, proc in enumerate(processes, 1):
                print(f"{i}. PID: {proc['pid']}")
                print(f"   Command: {proc['command']}")
                print()

        # Check for PID files
        pid_files = list(Path(self.project_dir).rglob("*.pid"))
        if pid_files:
            print(f"Found {len(pid_files)} PID file(s):")
            for pid_file in pid_files:
                print(f"  - {pid_file}")

        print("=" * 60 + "\n")

    def inspect(self):
        """Inspect active tasks and registered workers"""
        print("\n" + "=" * 60)
        print("CELERY INSPECTION")
        print("=" * 60)

        try:
            # Check active tasks
            result = subprocess.run(
                ["celery", "-A", self.app_name, "inspect", "active"],
                capture_output=True,
                text=True,
                cwd=self.project_dir,
            )
            print("\nActive Tasks:")
            print(result.stdout or "No active tasks")

            # Check stats
            result = subprocess.run(
                ["celery", "-A", self.app_name, "inspect", "stats"],
                capture_output=True,
                text=True,
                cwd=self.project_dir,
            )
            print("\nWorker Stats:")
            print(result.stdout or "No stats available")

        except Exception as e:
            print(f"Error inspecting: {e}")

        print("=" * 60 + "\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Manage Celery workers")
    parser.add_argument(
        "command",
        choices=["start", "stop", "force-stop", "restart", "status", "inspect"],
        help="Command to execute",
    )
    parser.add_argument(
        "--app", "-A", default="your_app", help="Celery app name (default: your_app)"
    )
    parser.add_argument(
        "--dir", "-d", default=None, help="Project directory (default: current)"
    )
    parser.add_argument(
        "--log-level", "-l", default="info", help="Log level (default: info)"
    )
    parser.add_argument(
        "--concurrency", "-c", type=int, default=None, help="Number of worker processes"
    )
    parser.add_argument(
        "--queues", "-Q", default=None, help="Comma-separated list of queues"
    )

    args = parser.parse_args()

    manager = CeleryManager(args.app, args.dir)

    if args.command == "start":
        manager.start(
            log_level=args.log_level, concurrency=args.concurrency, queues=args.queues
        )
    elif args.command == "stop":
        manager.stop_all(force=False)
    elif args.command == "force-stop":
        manager.stop_all(force=True)
    elif args.command == "restart":
        manager.restart(
            log_level=args.log_level, concurrency=args.concurrency, queues=args.queues
        )
    elif args.command == "status":
        manager.status()
    elif args.command == "inspect":
        manager.inspect()


if __name__ == "__main__":
    main()
