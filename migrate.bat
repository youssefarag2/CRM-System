@echo off
REM Activate the virtual environment
call ..\Scripts\activate

REM Make migrations
python manage.py makemigrations

REM Apply migrations
python manage.py migrate

REM Run the development server
python manage.py runserver


