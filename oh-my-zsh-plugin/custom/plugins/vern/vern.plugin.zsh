# vern.plugin.zsh

VERN=~/code/dev/vern/vern/vern_client.py

source ~/code/dev/vern/venv/bin/activate
export PATH=$PATH:~/code/dev/vern/vern/

function v4 { vern --model gpt-4o }
function vcp { cat ~/.local/share/vern/.ppid/session-ppid-$$/config.yaml }

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
	$VERN --use-sys code-generator "$@"
}

function vl {
	$VERN --use-sys latex-generator "$@"
}

function rprint {
	#PRINTER=Brother_HL_L8360CDW_series
	PRINTER=$(lpstat -d | awk -F': ' '{print $2}')
	if [[ -z $PRINTER ]]; then
		echo "set default printer with, ex: 'sudo lpadmin -p Brother_HL_L8360CDW_series -d Brother_HL_L8360CDW_series'"
	fi
	BASENAME=$1
	shift
	INGREDIENTS=$@
	echo $BASENAME
	echo $INGREDIENTS
	$VERN --use-sys recipe-generator --no-markdown $INGREDIENTS | tee $BASENAME.latex && pdflatex $BASENAME.latex && lpr -P $PRINTER $BASENAME.pdf
}

function rprint-edit {
	PRINTER=$(lpstat -d | awk -F': ' '{print $2}')
	if [[ -z $PRINTER ]]; then
		echo "set default printer with, ex: 'sudo lpadmin -p Brother_HL_L8360CDW_series -d Brother_HL_L8360CDW_series'"
	fi
	BASENAME=$1
	$VERN --use-sys recipe-generator --no-markdown --edit | tee $BASENAME.latex && pdflatex $BASENAME.latex && lpr -P $PRINTER $BASENAME.pdf
}


function vr {
	$VERN --use-sys recipe-generator "$@"
}
