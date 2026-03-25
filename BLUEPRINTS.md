# Cyclist — Automation Blueprints

These blueprints help you turn Cyclist data into actionable household automations. Copy these into your `blueprints/automation/` directory or use them as a guide for manual automations.

## 1. Bathroom Button (One-Click Period Logging)
Use a physical button (Zigbee/Matter) in the bathroom to log your period start instantly without opening an app.

```yaml
blueprint:
  name: Cyclist - Physical Button Period Log
  description: Log a period start when a physical button is pressed.
  domain: automation
  input:
    button_device:
      name: Button Device
      description: The physical button to use.
      selector:
        device:
          filter:
            - integration: zha
            - integration: zigbee2mqtt
    cyclist_entry:
      name: Cyclist Instance
      description: The Cyclist integration to update.
      selector:
        target:
          entity:
            integration: cyclist

trigger:
  - platform: device
    domain: mqtt # Example for Z2M, adjust for your button type
    device_id: !input button_device
    type: action
    subtype: single

action:
  - service: cyclist.log_period_start
    target: !input cyclist_entry
    data:
      date: "{{ now().date() }}"
```

---

## 2. Stock Up Notification (Proactive Partner Support)
Notify a partner 3 days before a predicted period so they can check for supplies (ibuprofen, chocolate, tampons).

```yaml
blueprint:
  name: Cyclist - Stock Up Notification
  description: Notify when a period is 3 days away.
  domain: automation
  input:
    cyclist_sensor:
      name: Next Period Sensor
      selector:
        entity:
          filter:
            - integration: cyclist
              domain: sensor
    notify_device:
      name: Device to notify
      selector:
        device:
          filter:
            - integration: mobile_app

trigger:
  - platform: numeric_state
    entity_id: !input cyclist_sensor
    below: 4 # Trigger when 3 days remain

condition:
  - condition: time
    after: "10:00:00"
    before: "20:00:00"

action:
  - service: notify.mobile_app_{{ device_entities(notify_device) | select('search', 'notify') | first }}
    data:
      title: "Cyclist Alert"
      message: "The period is predicted to start in 3 days. Time to check supplies!"
```

---

## 3. Fertility Goal Notification (Plan vs. Avoid)
Sends a goal-aware notification when the fertile window opens.

```yaml
blueprint:
  name: Cyclist - Goal Awareness Notification
  description: Send a notification when fertility changes, customized by your goal.
  domain: automation
  input:
    status_sensor:
      name: Fertility Status Sensor
      selector:
        entity:
          filter:
            - integration: cyclist
              domain: sensor
    goal_sensor:
      name: Goal Sensor
      selector:
        entity:
          filter:
            - integration: cyclist
              domain: sensor

trigger:
  - platform: state
    entity_id: !input status_sensor

action:
  - choose:
      # If Avoiding
      - conditions:
          - condition: state
            entity_id: !input goal_sensor
            state: "avoid"
          - condition: state
            entity_id: !input status_sensor
            state: "high_chance"
        sequence:
          - service: notify.persistent_notification
            data:
              title: "Cyclist: Caution"
              message: "You are in the fertile window. High chance of pregnancy today."
      
      # If Planning
      - conditions:
          - condition: state
            entity_id: !input goal_sensor
            state: "plan"
          - condition: state
            entity_id: !input status_sensor
            state: "peak_fertility"
        sequence:
          - service: notify.persistent_notification
            data:
              title: "Cyclist: Peak Time"
              message: "Peak fertility window is open! It's a great time to try."
```
