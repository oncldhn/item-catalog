# Item Catalog
Udacity Full Stack Web Developer Nanodegree - Item Catalog Project

##Files
```
catalog
├── static
    └── main.css
├── templates
    ├── addItem.html
    ├── categories.html
    ├── item.html
    ├── items.html
    ├── login.html
    ├── main.html
├── client_secrets.json
├── database_setup.py
├── itemcatalog.db
├── itemcatalog.py
├── populate_categories.py
└── README.md
```

##Running
1. run vagrant and browse catalog folder
2. execute FLASK_APP=itemcatalog.py flask run --host=0.0.0.0 command
3. the web application should be browsed from 127.0.0.1:5000 address
   because of the google sign-in callback domain registry
