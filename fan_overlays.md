# Raspberry Pi 5 Active Cooler - Fan Overlay Profiles

The Pi 5 has a built-in `cooling_fan` device tree node with these defaults:

| State | Temp Threshold | PWM | Duty Cycle |
|-------|---------------|-----|------------|
| 0     | < 50C (122F)  | 0   | Off        |
| 1     | 50C (122F)    | 75  | ~29%       |
| 2     | 60C (140F)    | 125 | ~49%       |
| 3     | 67.5C (153F)  | 175 | ~69%       |
| 4     | 75C (167F)    | 250 | ~98%       |

Each profile below has two options:
- **Persistent (reboot required):** Adds a `dtoverlay=pwm-fan` line to `/boot/firmware/config.txt`
- **Runtime (immediate, lost on reboot):** Writes directly to sysfs trip points

Sysfs paths:
- Trip points: `/sys/class/thermal/thermal_zone0/trip_point_{1-4}_temp`
- PWM value: `/sys/class/hwmon/hwmon2/pwm1` (0-255)
- PWM mode: `/sys/class/hwmon/hwmon2/pwm1_enable` (1=auto, 0=manual)

---

## Always On (Quiet)

Fan never fully stops. Low minimum speed to keep airflow while staying quiet.

| State | Temp     | PWM | Duty |
|-------|----------|-----|------|
| 0     | 40C (104F) | 40  | ~16% |
| 1     | 50C (122F) | 100 | ~39% |
| 2     | 60C (140F) | 175 | ~69% |
| 3     | 67.5C (153F) | 255 | 100% |

**Persistent (reboot required):**

```bash
sudo sed -i '/^dtoverlay=pwm-fan/d' /boot/firmware/config.txt
echo 'dtoverlay=pwm-fan,temp0=40000,temp0_speed=40,temp1=50000,temp1_speed=100,temp2=60000,temp2_speed=175,temp3=67500,temp3_speed=255' | sudo tee -a /boot/firmware/config.txt
echo "Always On (Quiet) profile applied. Reboot to activate."
```

**Runtime (immediate):**

```bash
echo 40000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_1_temp
echo 50000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_2_temp
echo 60000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_3_temp
echo 67500 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_4_temp
echo "Always On (Quiet) trip points applied immediately."
```

---

## Aggressive Cooling

Starts early at higher speeds. Good for sustained workloads or hot environments.

| State | Temp     | PWM | Duty |
|-------|----------|-----|------|
| 0     | 35C (95F)  | 75  | ~29% |
| 1     | 45C (113F) | 150 | ~59% |
| 2     | 55C (131F) | 200 | ~78% |
| 3     | 60C (140F) | 255 | 100% |

**Persistent (reboot required):**

```bash
sudo sed -i '/^dtoverlay=pwm-fan/d' /boot/firmware/config.txt
echo 'dtoverlay=pwm-fan,temp0=35000,temp0_speed=75,temp1=45000,temp1_speed=150,temp2=55000,temp2_speed=200,temp3=60000,temp3_speed=255' | sudo tee -a /boot/firmware/config.txt
echo "Aggressive Cooling profile applied. Reboot to activate."
```

**Runtime (immediate):**

```bash
echo 35000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_1_temp
echo 45000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_2_temp
echo 55000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_3_temp
echo 60000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_4_temp
echo "Aggressive Cooling trip points applied immediately."
```

---

## Silent (Late Start)

Fan stays off longer. Prioritizes silence over thermals. Fine for light/idle usage.

| State | Temp     | PWM | Duty |
|-------|----------|-----|------|
| 0     | 55C (131F) | 50  | ~20% |
| 1     | 65C (149F) | 125 | ~49% |
| 2     | 72C (161F) | 200 | ~78% |
| 3     | 80C (176F) | 255 | 100% |

**Persistent (reboot required):**

```bash
sudo sed -i '/^dtoverlay=pwm-fan/d' /boot/firmware/config.txt
echo 'dtoverlay=pwm-fan,temp0=55000,temp0_speed=50,temp1=65000,temp1_speed=125,temp2=72000,temp2_speed=200,temp3=80000,temp3_speed=255' | sudo tee -a /boot/firmware/config.txt
echo "Silent profile applied. Reboot to activate."
```

**Runtime (immediate):**

```bash
echo 55000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_1_temp
echo 65000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_2_temp
echo 72000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_3_temp
echo 80000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_4_temp
echo "Silent trip points applied immediately."
```

---

## Full Speed (Always Max)

Fan runs at 100% regardless of temperature. Maximum cooling, maximum noise.

**Persistent (reboot required):**

```bash
sudo sed -i '/^dtoverlay=pwm-fan/d' /boot/firmware/config.txt
echo 'dtoverlay=pwm-fan,temp0=20000,temp0_speed=255,temp1=30000,temp1_speed=255,temp2=40000,temp2_speed=255,temp3=50000,temp3_speed=255' | sudo tee -a /boot/firmware/config.txt
echo "Full Speed profile applied. Reboot to activate."
```

**Runtime (immediate):**

```bash
echo 0 | sudo tee /sys/class/hwmon/hwmon2/pwm1_enable
echo 255 | sudo tee /sys/class/hwmon/hwmon2/pwm1
echo "Fan set to full speed. Manual PWM mode enabled."
```

---

## Revert to Default

Removes custom overlay and restores stock Pi 5 fan behavior.

**Persistent (reboot required):**

```bash
sudo sed -i '/^dtoverlay=pwm-fan/d' /boot/firmware/config.txt
echo "Custom fan overlay removed. Stock behavior restored. Reboot to activate."
```

**Runtime (immediate):**

```bash
echo 1 | sudo tee /sys/class/hwmon/hwmon2/pwm1_enable
echo 50000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_1_temp
echo 60000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_2_temp
echo 67500 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_3_temp
echo 75000 | sudo tee /sys/class/thermal/thermal_zone0/trip_point_4_temp
echo "Stock fan behavior restored immediately."
```
