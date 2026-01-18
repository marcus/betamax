#!/bin/bash
# Simulated betamax keys file demo

clear
sleep 0.5

# Show the keys file content
printf '$ cat demo.keys\n'
sleep 0.5
printf '@set:cols:60\n'
printf '@set:rows:10\n'
printf '@sleep:300\n'
printf '@capture:demo.png\n'
sleep 1

# Show running betamax with keys file
printf '\n$ betamax '\''neofetch'\'' -f demo.keys\n'
sleep 1.5

# Simulated output
printf '\nSleeping 300ms...\n'
sleep 0.5
printf 'Captured: captures/demo.png\n'
printf 'Done\n'

# Keep session alive briefly
sleep 3
