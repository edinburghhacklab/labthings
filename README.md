# LabThings

Megarepo for all small lab thingy project scripts with no other home to go to

Better than only local!

## Checking out a project with sparse-checkout

```
git clone --no-checkout --depth=1 --filter=tree:0 git@github.com:edinburghhacklab/labthings.git
cd labthings/
git sparse-checkout set --no-cone /<project>
git checkout
```

## Adding a project

Create a subdirectory appropriately named with a README.md!

## Auto-updating scripts from this repo

Here is a cron example for keeping a script up to date on the working machine:

```
* * * * * cd /path/to/project && git pull && <any other commands>
```
