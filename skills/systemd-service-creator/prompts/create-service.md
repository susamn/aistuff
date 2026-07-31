# Example Prompts for Systemd Service Creator

## Scenario 1: Scaffold a background daemon service
"Create a systemd service for my new app at $WORKSPACE_PATH/services/my-daemon."

```bash
<SKILL_PATH>/scripts/manage.py scaffold \
  --name my-daemon \
  --exec "$WORKSPACE_PATH/services/my-daemon/start.sh" \
  --service-type simple \
  --unit-type service \
  --output-dir "$WORKSPACE_PATH/services/my-daemon"
```

## Scenario 2: Scaffold a scheduled timer and oneshot service
"Set up a daily systemd backup timer for my project at $WORKSPACE_PATH/services/db-backup."

```bash
<SKILL_PATH>/scripts/manage.py scaffold \
  --name db-backup \
  --exec "$WORKSPACE_PATH/services/db-backup/backup.sh" \
  --unit-type both \
  --schedule "daily" \
  --output-dir "$WORKSPACE_PATH/services/db-backup"
```
