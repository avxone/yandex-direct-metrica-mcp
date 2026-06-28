# tmux for Symphony

This note explains how to use `tmux` to monitor and control long-running Symphony lanes.

## What `tmux` does

`tmux` keeps terminal sessions alive in the background.

This is useful for Symphony because:

- the lane keeps running after you close a terminal tab;
- you can reconnect later;
- each lane can have its own persistent console.

## Current lane names

For `yandex.ad` the standard session names are:

- `yad-impl`
- `yad-review`
- `yad-pr`
- `yad-release`

They usually correspond to:

- implementation
- review
- PR publication
- release publication

## List running sessions

```bash
tmux list-sessions
```

Example output:

```text
yad-impl: 1 windows
yad-review: 1 windows
yad-pr: 1 windows
yad-release: 1 windows
```

## Attach to one session

Open one lane in the current terminal:

```bash
tmux attach -t yad-impl
```

Important:

- attach to one session at a time per terminal window;
- `attach` takes over the whole terminal.

If you want to watch multiple lanes at once, open multiple terminal tabs/windows.

Suggested layout:

- tab 1: `tmux attach -t yad-impl`
- tab 2: `tmux attach -t yad-review`
- tab 3: `tmux attach -t yad-pr`
- tab 4: `tmux attach -t yad-release`

## Detach without stopping the lane

To leave the view but keep the Symphony lane running:

1. press `Ctrl+b`
2. then press `d`

This is the most important tmux shortcut.

It detaches from the session and returns you to the normal shell.

## Reattach later

```bash
tmux attach -t yad-review
```

You reconnect to the same running lane.

## Kill one lane

To stop one Symphony lane completely:

```bash
tmux kill-session -t yad-pr
```

This kills the tmux session and the Symphony process running inside it.

## Kill all Symphony lanes

```bash
tmux kill-session -t yad-impl
tmux kill-session -t yad-review
tmux kill-session -t yad-pr
tmux kill-session -t yad-release
```

## Check whether the dashboards are alive

```bash
curl -s http://127.0.0.1:3321/ >/dev/null && echo impl-ok
curl -s http://127.0.0.1:3322/ >/dev/null && echo review-ok
curl -s http://127.0.0.1:3323/ >/dev/null && echo pr-ok
curl -s http://127.0.0.1:3324/ >/dev/null && echo release-ok
```

Standard ports:

- `3321` implementation
- `3322` review
- `3323` PR
- `3324` release

## Capture the current screen without attaching

Useful when you want a quick snapshot from a lane:

```bash
tmux capture-pane -pt yad-impl | tail -n 40
```

Examples:

```bash
tmux capture-pane -pt yad-review | tail -n 40
tmux capture-pane -pt yad-pr | tail -n 40
tmux capture-pane -pt yad-release | tail -n 40
```

## Typical control flow

### 1. Check sessions

```bash
tmux list-sessions
```

### 2. Watch implementation

```bash
tmux attach -t yad-impl
```

### 3. Leave implementation view

Press:

```text
Ctrl+b, then d
```

### 4. Check review lane quickly

```bash
tmux capture-pane -pt yad-review | tail -n 40
```

### 5. Open review interactively

```bash
tmux attach -t yad-review
```

## Common mistakes

### “I need to run all attach commands in one terminal”

No.

Use one `attach` command per terminal tab/window.

### “Detaching stops the process”

No.

Detaching only leaves the view. The lane keeps running.

### “Killing the terminal tab is the same as detach”

No.

Closing a normal attached terminal can break your view unexpectedly. Use:

- `Ctrl+b`, `d`

for a clean detach.

### “No sessions found”

That means the lanes are not currently running.

Check:

```bash
tmux list-sessions
```

If empty, the Symphony lanes need to be started again.

## Minimal cheat sheet

```bash
tmux list-sessions
tmux attach -t yad-impl
tmux attach -t yad-review
tmux attach -t yad-pr
tmux attach -t yad-release
tmux capture-pane -pt yad-impl | tail -n 40
tmux kill-session -t yad-impl
```

Detach shortcut:

```text
Ctrl+b, then d
```
