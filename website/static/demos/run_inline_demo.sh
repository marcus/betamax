#!/bin/bash
# Simulated betamax inline demo

# Clear and show prompt
clear
sleep 0.5

# Show the command being run
printf '$ betamax '\''echo Hello'\'' -- @sleep:500 @capture:hello.txt\n'
sleep 1.5

# Simulated output
printf '\nSleeping 500ms...\n'
sleep 0.5
printf 'Captured: captures/hello.txt\n'
printf 'Done\n\n'
sleep 0.5

# Show the captured output
printf '$ cat captures/hello.txt\n'
sleep 0.5
printf 'Hello from Betamax!\n'

# Keep session alive briefly
sleep 3
