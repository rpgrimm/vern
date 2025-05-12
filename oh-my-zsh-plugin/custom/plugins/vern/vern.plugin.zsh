# vern.plugin.zsh

SRC_DIR=~/code/dev/vern

export PYTHON3=$SRC_DIR/venv/bin/python3

vern() { $PYTHON3 $SRC_DIR/vern/vern_client.py "$@" }
v() { vern "$@" }
v4()  { vern --model gpt-4o "$@" }
vcp() { cat ~/.local/share/vern/.ppid/session-ppid-$$/config.yaml && cat ~/.local/share/vern/.ppid/session-ppid-$$/system.json }
vc() { vern --use-sys code-generator "$@" }

function vern-code-gen { vern --use-sys code-generator "$@" }


function ve {
	tempfile=$(mktemp /tmp/editor.XXXXXX)
	${EDITOR:-vim} "$tempfile"
	$VERN --stdin < "$tempfile"
	rm "$tempfile"
}

function vs { vern --use-sys sophisticated "$@" }



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
