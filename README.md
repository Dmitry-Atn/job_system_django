# job_system_django

Running simple python jobs.

## Warning

This system can't be used on *production environment* since the functionality includes
 security breach such as unauthorized access to the job running, 
 and unlimited job permissions.

## Structure
I adapted the code from [this project](https://github.com/sjl/django-hoptoad/blob/master/hoptoad/handlers/utils/threadpool.py).
Jobs being executed by reusable threads from a thread pool.

## Installation

### Requirements
- OS Windows / *nix
- python 3.7
- pip
- git

Execute in command line
```buildoutcfg
git clone git@github.com:Dmitry-Atn/job_system_django.git
cd job_system_django
pip install requirements.txt
```

## Usage

```buildoutcfg
cd job_system
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```
- Open in browser `http://localhost:8000/`
- Click 'Create New'
- Create new job, for example:
```
from time import sleep
sleep(30)
print("Done!!!")
```
- Run the job

## Features
- [x] Creating and running python jobs
- [x] Tracking jobs lifecycle
- [x] Jobs can run concurrently
- [ ] Running in memory
- [ ] Scheduling
- [ ] Production readygit