# copy all necessary files and folders to remote computer

import os

#inst_name='im@small-1'
#local_cmd = '--project cam-usa --zone us-central1-c '

instance= 'mini'
remote_user = 'morigo2015'
local_cmd = ' '
# additionally to set _remote_user_name in  cloud/cam_detect_cfg.py

print(f'instance={instance}  remote_user={remote_user} local_cmd={local_cmd}')

os.chdir('/home/im/mypy/cam_detect/')
print(f'local_cur_dir = {os.getcwd()} ')

def cmd(cmd_str):
    print(f'cmd_str:{cmd_str}')
    r = os.system(cmd_str)
    if r != 0:
        print(f'error while execte system()={r}')
        exit(0)

cmd(f'gcloud compute scp {local_cmd} cloud/setup_cloud_computer.sh   {remote_user}@{instance}:/home/{remote_user}')
cmd(f'gcloud compute ssh {remote_user}@{instance} --command ./setup_cloud_computer.sh')

cmd(f'gcloud compute scp {local_cmd} src/*.py    {remote_user}@{instance}:/home/{remote_user}/mypy/cam_detect/src')
cmd(f'gcloud compute scp {local_cmd} cloud/*.py  {remote_user}@{instance}:/home/{remote_user}/mypy/cam_detect/src')

cmd(f'gcloud compute scp {local_cmd} production/models/*           {remote_user}@{instance}:/home/{remote_user}/mypy/cam_detect/production/models')
cmd(f'gcloud compute scp {local_cmd} production/face_dataset/*.pkl {remote_user}@{instance}:/home/{remote_user}/mypy/cam_detect/production/face_dataset')

