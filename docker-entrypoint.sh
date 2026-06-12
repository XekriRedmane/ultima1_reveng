#!/bin/bash
# Git identity for the agent's commits (override via compose environment).
git config --global user.name  "${GIT_USER_NAME:-RE Agent}"
git config --global user.email "${GIT_USER_EMAIL:-re-agent@localhost}"

# Redirect Claude state to the host-bind-mounted directory so sessions,
# settings, and agent memory survive container restarts.
# Mounting the directory (not the .json file directly) preserves atomic-rename
# semantics — Claude Code writes .claude.json.tmp + rename, which only works
# when the rename target lives in a real directory inode.
HOST_STATE=/host-state
mkdir -p "$HOST_STATE/.claude"
[ -L "$HOME/.claude" ] || rm -rf "$HOME/.claude"
ln -sfn "$HOST_STATE/.claude" "$HOME/.claude"
ln -sfn "$HOST_STATE/.claude.json" "$HOME/.claude.json"

# Copy host SSH credentials (read-only mount) so git push over SSH works.
if [ -d /mnt/host-ssh ]; then
    mkdir -p "$HOME/.ssh"
    chmod 700 "$HOME/.ssh"
    for key in id_ed25519 id_rsa; do
        [ -f "/mnt/host-ssh/$key" ] && cp "/mnt/host-ssh/$key" "$HOME/.ssh/" && chmod 600 "$HOME/.ssh/$key"
        [ -f "/mnt/host-ssh/$key.pub" ] && cp "/mnt/host-ssh/$key.pub" "$HOME/.ssh/" && chmod 644 "$HOME/.ssh/$key.pub"
    done
    [ -f /mnt/host-ssh/known_hosts ] && cp /mnt/host-ssh/known_hosts "$HOME/.ssh/" && chmod 644 "$HOME/.ssh/known_hosts"
    ssh-keyscan -t ed25519,rsa github.com >> "$HOME/.ssh/known_hosts" 2>/dev/null
    sort -u "$HOME/.ssh/known_hosts" -o "$HOME/.ssh/known_hosts"
fi

exec "$@"
