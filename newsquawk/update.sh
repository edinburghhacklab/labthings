#!/bin/bash

cd /home/pi/labthings/newsquawk
PULL_RES="$(git pull)"
if [[ "$PULL_RES" = "Already up to date." ]]; then
	# No changes
	echo "No changes."
	exit 0
else
	echo "Updated, restarting..."
	sudo systemctl daemon-reload
	sudo systemctl restart squawk.service
	echo "Finished."
fi
