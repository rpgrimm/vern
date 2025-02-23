TXT_FILE=pg2383.txt
if [ ! -e "$TXT_FILE" ] ; then
        wget -q https://www.gutenberg.org/cache/epub/2383/"$TXT_FILE"
fi

awk '/THE PROLOGUE\./ && !started {flag=1; started=1} /Notes to the Prologue/ && flag {flag=0} flag' "$TXT_FILE" > canterbury-tales-prologue.txt
