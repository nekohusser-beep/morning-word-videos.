# Queue (the warehouse)
One JSON file per finished video in queue/ready/. The feeder robot (feeder.yml, daily ~3 AM ET) posts it to every listed channel in Buffer when that channel has room, then moves it to queue/posted/.

```json
{
  "kind": "short",
  "due": "2026-11-14T05:00:00-05:00",
  "video": "https://github.com/nekohusser-beep/morning-word-videos./releases/download/TAG/file.mp4",
  "channels": {
    "youtube":   {"title": "IQ Vid title", "text": "IQ Vid description + tags"},
    "tiktok":    {"text": "caption + hashtags"},
    "instagram": {"text": "caption + hashtags"},
    "facebook":  {"text": "caption"}
  }
}
```
kind = "short" or "long". IQ Vid must run before a file goes into ready/. Facebook posts only after its Buffer channel id is added to queue/channels.json.
