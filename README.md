# Nutria-DB
Food database.

## Installation

For development first clone this repository and enter the Folder.

```
cd Nutria-DB
```

Then create a virtual environment:

```
python -m venv env
source env/bin/activate
```

Now install the dependencies:

```
pip install -r requirements.txt
```

This is sufficient for development. If you want to use Nutria-DB with Maria for production you need to install the
appropriate database client:

```
pip install mysqlclient
```

Now you can set up your database:

```
cd nutriaDB
python manage.py migrate
python manage.py createsuperuser
python manage.py initial_data
```

The last command populates your database with food data from the fixtures in the repository.

Run the development server with:

```
python manage.py runserver
```