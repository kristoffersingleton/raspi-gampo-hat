#!/usr/bin/env python3
"""
Raspberry Pi 5 System Monitor
Displays Pi-specific metrics including Hailo AI accelerator status
There were several times when it would fail "Not ready" when I was sure it was ready.
Run this in a separate terminal window that is at least 90 columns wide - ( done in rich not curses )
btop was just too much - and the native terminal wasnt as pretty without the UTF ( btop --utf-force ) 
However - remoting in from the SSH on Raspberry PI Connect and doign btop was pretty great.
"""

import subprocess
import time
import re
from pathlib import Path
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

class PiMonitor:
    def __init__(self):
        self.console = Console()
        self.frame = 0

    def run_cmd(self, cmd):
        """Run command and return output, return None on error"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def read_file(self, path):
        """Read file content, return None on error"""
        try:
            return Path(path).read_text().strip()
        except Exception:
            return None

    def get_activity_indicator(self):
        """Create a bouncing activity indicator"""
        width = 20
        positions = list(range(width)) + list(range(width-2, 0, -1))
        pos = positions[self.frame % len(positions)]
        indicator = ['.'] * width
        indicator[pos] = 'o'
        return '[' + ''.join(indicator) + ']'

    def get_cpu_temp(self):
        """Get CPU temperature via vcgencmd"""
        output = self.run_cmd("vcgencmd measure_temp")
        if output:
            match = re.search(r"temp=([\d.]+)", output)
            if match:
                temp = float(match.group(1))
                temp_f = temp * 9 / 5 + 32
                color = "green" if temp < 60 else "yellow" if temp < 75 else "red"
                return f"[{color}]{temp}C ({temp_f:.1f}F)[/{color}]"
        return "[dim]N/A[/dim]"

    def get_cpu_freq(self):
        """Get current ARM CPU frequency"""
        output = self.run_cmd("vcgencmd measure_clock arm")
        if output:
            match = re.search(r"frequency\(\d+\)=(\d+)", output)
            if match:
                freq_mhz = int(match.group(1)) / 1000000
                return f"{freq_mhz:.0f} MHz"
        return "N/A"

    def get_throttle_status(self):
        """Get throttling status - critical for Pi health"""
        output = self.run_cmd("vcgencmd get_throttled")
        if output:
            match = re.search(r"throttled=0x([0-9a-fA-F]+)", output)
            if match:
                throttle_code = int(match.group(1), 16)
                if throttle_code == 0:
                    return "[green]OK[/green]"

                issues = []
                if throttle_code & 0x1:
                    issues.append("[red]Under-voltage![/red]")
                if throttle_code & 0x2:
                    issues.append("[yellow]ARM freq capped[/yellow]")
                if throttle_code & 0x4:
                    issues.append("[yellow]Throttled[/yellow]")
                if throttle_code & 0x8:
                    issues.append("[red]Soft temp limit[/red]")

                # Historical flags
                if throttle_code & 0x10000:
                    issues.append("[dim]Under-voltage (past)[/dim]")
                if throttle_code & 0x20000:
                    issues.append("[dim]Throttled (past)[/dim]")

                return " ".join(issues) if issues else f"[yellow]0x{throttle_code:x}[/yellow]"
        return "[dim]N/A[/dim]"

    def get_voltage(self, component="core"):
        """Get voltage for component"""
        output = self.run_cmd(f"vcgencmd measure_volts {component}")
        if output:
            match = re.search(r"volt=([\d.]+)V", output)
            if match:
                return f"{match.group(1)}V"
        return "N/A"

    def get_fan_speed(self):
        """Get PWM fan speed in RPM"""
        fan_input = self.read_file("/sys/class/hwmon/hwmon2/fan1_input")
        if fan_input and fan_input != "0":
            rpm = int(fan_input)
            color = "green" if rpm > 1000 else "yellow" if rpm > 0 else "red"
            return f"[{color}]{rpm} RPM[/{color}]"
        return "[dim]Off/N/A[/dim]"

    def get_hailo_info(self):
        """Get Hailo AI accelerator information"""
        info = {}

        # Check if device exists
        lspci_out = self.run_cmd("lspci | grep -i hailo")
        if not lspci_out:
            return {"status": "[red]Not detected[/red]"}

        info["pcie"] = lspci_out.split(":", 2)[-1].strip() if lspci_out else "N/A"

        # Get firmware info
        fw_out = self.run_cmd("hailortcli fw-control identify 2>/dev/null")
        if fw_out:
            fw_match = re.search(r"Firmware Version: ([\S]+)", fw_out)
            arch_match = re.search(r"Device Architecture: ([\S]+)", fw_out)
            if fw_match:
                info["firmware"] = fw_match.group(1)
            if arch_match:
                info["arch"] = arch_match.group(1)

        # Try to get temperature (may not always be available)
        temp_out = self.run_cmd("hailortcli fw-control temperature 2>/dev/null")
        if temp_out:
            temp_match = re.search(r"temperature: ([\d.]+)", temp_out)
            if temp_match:
                temp = float(temp_match.group(1))
                temp_f = temp * 9 / 5 + 32
                color = "green" if temp < 70 else "yellow" if temp < 85 else "red"
                info["temp"] = f"[{color}]{temp}C ({temp_f:.1f}F)[/{color}]"

        info["status"] = "[green]Active[/green]"
        return info

    def get_pcie_devices(self):
        """Get PCIe device list"""
        output = self.run_cmd("lspci")
        if output:
            devices = []
            for line in output.split("\n"):
                if line.strip():
                    # Format: 0001:01:00.0 Device: Description
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        devices.append({"addr": parts[0], "desc": parts[1]})
            return devices
        return []

    def get_memory_info(self):
        """Get memory usage"""
        output = self.run_cmd("free -h | grep Mem")
        if output:
            parts = output.split()
            if len(parts) >= 3:
                return {"total": parts[1], "used": parts[2], "free": parts[3] if len(parts) > 3 else "N/A"}
        return {"total": "N/A", "used": "N/A", "free": "N/A"}

    def create_system_table(self):
        """Create main system status table"""
        table = Table(title="Raspberry Pi 5 System Status", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", width=30)

        table.add_row("CPU Temperature", self.get_cpu_temp())
        table.add_row("CPU Frequency", self.get_cpu_freq())
        table.add_row("Throttle Status", self.get_throttle_status())
        table.add_row("Core Voltage", self.get_voltage("core"))
        table.add_row("Fan Speed", self.get_fan_speed())

        mem = self.get_memory_info()
        table.add_row("Memory", f"{mem['used']} / {mem['total']}")

        return table

    def create_hailo_table(self):
        """Create Hailo AI accelerator table"""
        table = Table(title="Hailo AI Accelerator", show_header=True, header_style="bold blue")
        table.add_column("Property", style="cyan", width=20)
        table.add_column("Value", width=30)

        hailo = self.get_hailo_info()

        table.add_row("Status", hailo.get("status", "N/A"))
        if "pcie" in hailo:
            table.add_row("Device", hailo["pcie"])
        if "arch" in hailo:
            table.add_row("Architecture", hailo["arch"])
        if "firmware" in hailo:
            table.add_row("Firmware", hailo["firmware"])
        if "temp" in hailo:
            table.add_row("Temperature", hailo["temp"])

        return table

    def create_pcie_table(self):
        """Create PCIe devices table"""
        table = Table(title="PCIe Devices", show_header=True, header_style="bold green")
        table.add_column("Address", style="yellow", width=15)
        table.add_column("Description", width=50)

        devices = self.get_pcie_devices()
        for dev in devices:
            table.add_row(dev["addr"], dev["desc"])

        if not devices:
            table.add_row("N/A", "[dim]No devices found[/dim]")

        return table

    def create_display(self):
        """Create the complete display layout"""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="system", size=10),
            Layout(name="bottom")
        )

        layout["bottom"].split_row(
            Layout(name="hailo"),
            Layout(name="pcie")
        )

        # Create header with activity indicator
        activity = self.get_activity_indicator()
        header_text = Text(f"Pi Monitor - Live {activity}", style="bold cyan", justify="center")
        layout["header"].update(Panel(header_text, style="blue"))

        layout["system"].update(self.create_system_table())
        layout["hailo"].update(self.create_hailo_table())
        layout["pcie"].update(self.create_pcie_table())

        return layout

    def run(self, refresh_rate=1.0):
        """Run the monitor with live updates"""
        try:
            with Live(self.create_display(), refresh_per_second=4, console=self.console) as live:
                while True:
                    time.sleep(refresh_rate)
                    self.frame += 1
                    live.update(self.create_display())
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Monitor stopped by user[/yellow]")

if __name__ == "__main__":
    monitor = PiMonitor()
    monitor.run(refresh_rate=1.0)
