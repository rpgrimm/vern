# vern.plugin.zsh

CLIENT=~/code/vern/vern_client.py

function vern() {
    if [ ! -e ~/.local/share/vern/session-$$ ] ; then
            $CLIENT --new-s $$ $@
    fi
    $CLIENT --use-s $$ $@
}

function fvern() {
    cat $1 | $CLIENT --use-s $$
}

function cvern() {
    echo $@ | $CLIENT -use-s $$ | tee -a code.$$.output.txt
}

function vern_model() {
    $CLIENT --use-s $$ --model $@
}

function vern_role() {
    $CLIENT --use-s $$ --new-r $@
}

function vern_linux() {
    $CLIENT --use-s $$ --new-r 'Act as an expert on Linux user space, kernel, coding, scripting, and debugging'
}

function cvern() {
    $CLIENT --use-s $$ -i -s
}

function vern_chef() {
  local session_name="vern-chef"
  local command="vern_role expert and patient american chef knowledgeable of all the worlds cuisine and history"

  # Check if the session exists
  if tmux has-session -t $session_name 2>/dev/null; then
    echo "Attaching to existing tmux session: $session_name"
    tmux attach-session -t $session_name
  else
    echo "Creating new tmux session: $session_name"
    tmux new-session -d -s $session_name
    tmux send-keys -t $session_name "$command" C-m
    tmux attach-session -t $session_name
  fi
}

function vern_trole() {
  local session_name=$1
  shift
  local command=("$@")

  # Check if the session exists
  if tmux has-session -t $session_name 2>/dev/null; then
    echo "Attaching to existing tmux session: $session_name"
    tmux attach-session -t $session_name
  else
    echo "Creating new tmux session: $session_name"
    tmux new-session -d -s $session_name
    tmux send-keys -t $session_name "$CLIENT --use-s $session_name --new-r $command" C-m
    tmux send-keys -t $session_name "$CLIENT --use-s $session_name -i" C-m
    tmux attach-session -t $session_name
  fi
}
