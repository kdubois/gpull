# gpull (python)
Do git commands (git pull, git checkout) on multiple repositories, or even multiple servers.

## Instructions:
- Rename the settings_example.yaml file to settings.yaml and modify it to your needs
- run python gpull.py -h to see all options.  You can also directly run gpull_local.py if you want to simply pull on local repositories.
- If you want to use the gpull remote feature, you will need to deploy the code to your servers as well.
Essentially the gpull.py script will try to ssh into your server and run the gpull_local.py script.  Beware that this may constitute a security hazard.

## Todo:
- Unit tests
- Improve security 
