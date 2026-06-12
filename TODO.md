# TODO

This file is the **loop state** for the autonomous RE process (see the
"Autonomy protocol" in `reveng.md`). Milestone entries at the top record
what each round finished and learned; the open work queue, structural
items, and blocked list live at the bottom. Every round updates this
file before committing. A fresh session resumes from `/re-status` output
plus this file — never by re-deriving history.

## Work queue

- [ ] Round 0: `/bootstrap` — extract reference binaries from the disk
      image, write `targets.json`, document the boot chain and disk
      layout, fill in the TODO(bootstrap) sections of CLAUDE.md and
      main.nw

## Blocked

(nothing blocked — when an item resists analysis, record here what was
tried and what evidence would unblock it, then move on)
