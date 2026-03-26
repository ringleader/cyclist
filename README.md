# <img src="brand/icon.png" width="80" height="80" align="right" /> Cyclist — Home Assistant Menstrual Cycle Tracker

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![Hass](https://img.shields.io/badge/Home%20Assistant-Integration-blue.svg?style=for-the-badge)](https://home-assistant.io)

A Home Assistant custom component that tracks menstrual cycles and surfaces fertility awareness data at a glance. Designed for privacy-conscious users who want to avoid or plan pregnancy using both calendar-based predictions and physiological symptoms.

> [!WARNING]
> **Medical Disclaimer:** This is a personal home automation tool, not a medical device. Always combine with other methods for contraception and consult with a professional.

---

## 🚀 Features

- **Privacy First:** All data is stored locally in your Home Assistant instance. No cloud, no subscriptions.
- **Calendar Predictions:** Automated 3-month forward-looking projections for periods and fertile windows.
- **Advanced Mode (Symptothermal Method):** Optional tracking for BBT, CM, and LH to confirm ovulation with precision.
- **Goal-Oriented:** Configure your goal as "Plan Pregnancy", "Avoid Pregnancy", or "Just Tracking" to receive tailored status updates.
- **Service Integration:** Easily log data from physical buttons, NFC tags, or custom dashboards.

---

## 📦 Installation

### HACS (Recommended)
1. [Fork this repository](https://github.com/ringleader/cyclist/fork).
2. Open **HACS** in Home Assistant.
3. Go to **Integrations** > **Custom Repositories**.
4. Add `https://github.com/your-username/cyclist` as an **Integration**.
5. Install **Cyclist** and restart Home Assistant.

### Manual
1. Copy the `custom_components/cyclist` folder to your `<config_dir>/custom_components/` directory.
2. Restart Home Assistant.

---

## ⚙️ Configuration

1. Go to **Settings > Devices & Services**.
2. Click **Add Integration** and search for **Cyclist**.
3. Configure your typical **Cycle Length** and **Period Duration**.
4. Set your primary **Goal**.

---

## 📈 Advanced Tracking

When you provide physiological data, Cyclist automatically upgrades from simple calendar estimates to data-driven confirmations.

- **Basal Body Temperature (BBT):** Confirm ovulation via the 3/6 rule (3 high temperatures above the previous 6).
- **Cervical Mucus (CM):** Identify your "Peak Day" based on high-quality fertile mucus.
- **LH Test Strips:** Record positive tests to identify the start of the fertile window.

### Available Sensors
- `sensor.cyclist_confirmed_ovulation`: Shows the cycle day ovulation was confirmed via symptoms.
- `sensor.cyclist_peak_day`: Shows the day of the detected CM or LH peak.
- `sensor.cyclist_fertility`: Dynamic status (Fertile, Low, Safer).
- `calendar.cyclist_predictions`: View your future cycle projections.

---

## 🛠️ Services

### `cyclist.log_period_start`
Mark the start of a period. Accepts an optional `date:` for backdating.

### `cyclist.log_bbt`, `cyclist.log_cm`, `cyclist.log_lh`
Log your daily observations directly from the UI or automations.

### `cyclist.log_symptom`
Quickly log common symptoms (cramps, headache, etc.) for easy automation access.

---

## 📊 Dashboard Example

Check the `lovelace_example.yaml` file for a complete vertical stack configuration to build your perfect cycle dashboard.

---

## 🤝 Support & Feedback

If you enjoy this integration, feel free to open an issue or pull request on GitHub!
