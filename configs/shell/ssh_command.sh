host[1]="devvm1773.nao0 (tmux)"
host[2]="devvm1773.nao0"
host[3]="localhost (tmux)"
top=3

full[1]="devvm1773.nao0.facebook.com"
full[2]="devvm1773.nao0.facebook.com"

#host[3]="alpha-pi"
#full[3]="192.168.0.21"

echo "Commander, where can I ssh you?"

echo "  (0) localhost"
echo -e "  (1) ${host[1]}\t\t(default)"
for i in $(seq 2 $top) ; do
  echo "  ($i) ${host[$i]}"
done

echo
echo -n "Destination [0-$top]: "
while true ; do
  read
  if [[ "$REPLY" == "" ]] ; then REPLY=1 ; fi
  if test `echo "$REPLY" | egrep "^[0-9]*$"` ; then
    if [[ "$REPLY" -ge 0 && "$REPLY" -le "$top" ]] ; then break ; fi
    echo -n "We haven't conquered that host yet. [0-$top]: "
  else
    echo -n "That destination is above your pay grade, sir. [0-$top]: "
  fi
done

if [[ "$REPLY" -ne "0" ]] ; then
  if [[ "$REPLY" -eq "3" ]] ; then
    tmux a
  else
    where="${full[$REPLY]}"

    echo "ssh'ing into $where"
    if [[ "$REPLY" == "1" || "$REPLY" == "4" ]] ; then
      echo "Automatically starting up tmux"
      ssh -t $where 'tmux attach -d'
      #mosh -6 $where -- tmux a
    else
      ssh $where
      #mosh -6 $where
    fi
  fi
fi
