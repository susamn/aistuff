# Output contract (schema 1)

The pipeline produces a JSON artifact listing all personal systemd units attached to `personal-services.target`.

```json
{
  "schema": 1,
  "id": "personal-services-list",
  "count": 2,
  "units": [
    {
      "unit": "sys-manager-cleanup.timer",
      "state": "active"
    },
    {
      "unit": "rclone-sync@obsidian.timer",
      "state": "inactive"
    }
  ]
}
```

Summary projection output format:

```
<unit_name>   <state>
<artifact>: /abs/path/to/artifact.json
```
