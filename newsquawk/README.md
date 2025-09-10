# NEWSQUAWK

Hacked together with ungodly shit

all problems may be solved with a newer pi but THATS NOT THE POINT (allegedly)

## Sysadmin

* Systemctl service defined in `squawk.service`, symbolic link in `/etc/systemd/system/squawk.service`

* Auto updates self from this git, logic defined in `update.sh`, last update will be logged to `latest.log`. Includes reloading systemctl for modifying service file.

* `latest.log` is available publically at http://squawk.hacklab/latest.log

## Notes

* RPi.GPIO was modified locally at some point to support this older model of pi - library seems to work fine with updated version now as far as we can tell, but be warned (old library directory backed up just in case at RPi-backup.zip)

* Updated to use UV as a package manager, though syncing with requirements.txt seems to remove the module botocore for some reason even though it's still needed. If this happens, fix with `uv pip install boto3`.

* Auto-update can sometimes fail if git-pull results in needing `git sparse-checkout reapply` - running this command and reloading will fix

* Touching in any way, shape or form may cause painful and irreversible effects, to the pi or to you.

*Last touched by vgorl 09/2025*
