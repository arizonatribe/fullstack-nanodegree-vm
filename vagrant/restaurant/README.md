# Udacity FullStack Foundations Project
This project demonstrates a full web application by applying a RESTful web api pattern,
relational database, OAuth2 authentication, and front-end user inferface development.
Building on the generalized Python explored up until this point, here we are actually
making use of a robust web framework in __Flask__. This streamlines the code we can write,
especially in HTML being able to receive data from the server.

The subject matter being explored in this project is a restaurant and menu creation tool.
Users of this application can expect to create, remove, or alter Restaurants as well as their
menu items.

### This project uses a relational database to keep track of:
* A Restaurant
* A Menu Item for that Restaurant

### This project uses server-side scripting to:
* create/update/read/delete a restaurant
* create/update/read/delete a restaurant's menu item
* list all restaurants
* list all menu items

### Running the project
If the dependencies have been installed and you've followed the steps in the general
whole project instructions (for setting up Vagrant and virtual box), then your vm
is up and running and you've ssh'd into it.

This should return a prompt that shows you logged in under the generic username
"vagrant". Now you need to move yourself to the `/vagrant/restaurant/` subfolder:

```
cd /vagrant/restaurant/
```
First, we'll need to setup the database from the python shell:

```
python database_setup.py
```

After we have the database, it would be useful to seed it with a basic list of restaurants and menu items.
Run the lotsofmenus script from the python shell to begin this process.

```
python lotsofmenus.py
```

Now, we're ready to run the project, so launch the project file from the python shell.

```
python project.py
```

With the python server up and running, we can now point our browser to it and interact with the
application's user interface. Open your browser and go to `http://localhost:5000/login`

From this login page you'll be able to sign in using your Google credentials. After it confirms the
basic permissions required, you'll be redirected to the home page of the application itself.

Here, you'll see a listing of every restaurant in the database. Each restaurant name itself is also
a link to that restaurant's menu, so you can either jump away to one of those restaurant's menus or
you can add to, remove or rename any of the restaurants listed here on this page. The menu restaurant
menus themselves mirror this same set of options with the ability to add to, remove from, or alter
menus for a given restaurant. The form you fill out to create or alter a menu item will provide you
with fields to set the name, pricing, full description, categorization and even upload a picture.

That about sums up the functionality being demonstrated here.

### API Endpoints
If you are simply trying to obtain information in a raw format, without wishing to interact with the application, you can hit the API endpoints directly and view in either JSON or Atom feed formats:

* `/restaurants/JSON` - [GET] Retrieves a list of restaurants in JSON format
* `/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON` - [GET] Retrieves a menu item in JSON format
* `/restaurants/<int:restaurant_id>/menu/JSON` - [GET] Retrieves a restaurant's menu in JSON format
* `/restaurants/atom` - [GET] Retrieves a list of restaurants in Atom feed format
* `/restaurants/<int:restaurant_id>/menu/<int:menu_id>/atom` - [GET] Retrieves a menu item in Atom feed format
* `/restaurants/<int:restaurant_id>/menu/atom` - [GET] Retrieves a restaurant's menu in Atom feed format

Otherwise, the APIs which the application was built around are listed below, any of which can be opened in a browser or bookmarked to create a shortcut to a give page:

* `/restaurants/<int:restaurant_id>/<int:menu_id>/delete/` - [GET, POST] Retrieves the page to remove a menu item for a restaurant and receives the user's attempt
* `/restaurants/<int:restaurant_id>/<int:menu_id>/edit/` - [GET, POST] Retrieves the page to alter a menu item for a restaurant and receives the user's attempt
* `/restaurants/<int:restaurant_id>/new/` - [GET, POST]Retrieves the page to create a new menu item for a restaurant and receives the user's attempt
* `/restaurants/<int:restaurant_id>/` - [GET] Lists all the menu items for a restaurant
* `/restaurants/<int:restaurant_id>/delete/` - [GET, POST] Retrieves the page to remove a restaurant and receives the user's attempt
* `/restaurants/<int:restaurant_id>/edit/` - [GET, POST] Retrieves the page to rename a restaurant and receives the user's attempt
* `/restaurants/new/` - [GET, POST] Retrieves the page to create a restaurant and receives the user's attempt
* `/restaurants/` - [GET] Lists all the restaurants
* `/gdisconnect` - [POST] Logs a user out
* `/gconnect` - [POST] Logs a user in
* `/login` - [GET] Retrieves the login page
