# vern.plugin.zsh

VERN=~/code/dev/vern/vern/vern_client.py

source ~/code/dev/vern/venv/bin/activate
export PATH=$PATH:~/code/dev/vern/vern/

function v4 { vern --model gpt-4o }
function vcp { cat ~/.local/share/vern/.ppid/session-ppid-$$/config.yaml }
set -o vi

function vern-code-gen { vern --use-sys code-generator "$@" }


function v {
	$VERN "$@"
}

function ve {
	tempfile=$(mktemp /tmp/editor.XXXXXX)
	${EDITOR:-vim} "$tempfile"
	$VERN --stdin < "$tempfile"
	rm "$tempfile"
}

function vs {
	$VERN --use-sys sophisticated "$@"
}

function vc {
	$VERN --use-sys code-generator
}
