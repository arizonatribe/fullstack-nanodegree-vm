import datetime
from urlparse import urljoin
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.contrib.atom import AtomFeed
app = Flask(__name__)

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User

#For Oauth credentials
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

# Connect to the restaurants database
engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

def generateNonce():
    """

    Returns: Randomly generated alphanumeric string

    """
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))

def isLoggedIn():
    """

    Returns: A boolean value indicating if the user is logged in

    """
    return formHasMember(login_session, 'username')

def formHasMember(form, name):
    """
    Args:
        form: an HTML form submitted in a POST request
        name: a string value representing the expected member in the form to check for

    Returns: A boolean value indicating if the member was found in the form (and is not `None`)

    """
    if not form or not name or name not in form:
        return False
    if not form[name] or form[name] == 'None':
        return False
    else:
        return True

# Create a state token to help guard against forged requests
@app.route('/login')
def showLogin():
    """

    Returns: An HTML page for the user to login

    """
    state = generateNonce()
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    """

    Returns: An HTTP response to a AJAX request to authenticate user a 3rd party OAuth provider

    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Retrieve the user's id or create one
    user_id = getUserID(data['email'])
    login_session['user_id'] = autoCreateUserIfNone(user_id)

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

@app.route('/gdisconnect')
def gdisconnect():
    """

    Returns: An HTTP response to the request to sign out of the site

    """
    if not formHasMember(login_session, 'username'):
        flash("User is not currently logged in")
    else:
        url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['credentials']
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]

        # If logout through the OAuth provider was successful, remove the user from the current session
        if result['status'] == '200':
            del login_session['credentials']
            del login_session['gplus_id']
            del login_session['username']
            del login_session['email']
            del login_session['picture']

            flash("User has been logged out successfully")
        else:
            flash("Attempted to log the user out, but failed to revoke their token; please try again")

    return redirect(url_for('showRestaurants'))

def autoCreateUserIfNone(user_id):
    """

    Args:
        user_id: An optional integer value identifying an existing user (which will be validated)

    Returns: An integer value uniquely identifying the existing or newly created user

    """
    if not user_id:
        return createUser(login_session)
    else:
        user = getUserInfo(user_id)
        if not user or not user.id:
            return createUser(login_session)
        else:
            return user.id

def createUser(login_session):
    """

    Args:
        login_session: The current session under which `username`, `email`, and `picture` might all be found

    Returns: An integer value representing the unique ID of the successfully created new user

    """
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])

    session.add(newUser)
    session.commit()

    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    """

    Args:
        email: An email address unique to a specific user account

    Returns: An integer value representing the unique id for a given user (None if it wasn't found)

    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

@app.route('/')
@app.route('/restaurants/', methods=['GET'])
def showRestaurants():
    """

    Returns: A page containing a list of all restaurants in the database

    """
    restaurants = session.query(Restaurant).all()
    if not restaurants:
        flash("no restaurants exist yet, try creating some")
    return render_template('restaurants.html', restaurants=restaurants, auth=isLoggedIn())

@app.route('/restaurants/new/', methods=['GET', 'POST'])
def newRestaurant():
    """

    Returns: Responds to the user request to show the page for creating a new restaurant and also handles their posted
    attempt at creating one

    """
    # First, make sure the user is authenticated (cannot create a restaurant if not logged in)
    if not isLoggedIn():
        return redirect('/login')
    # Receive the attempt to create a new restaurant or return the page for the user to create one
    elif request.method == 'POST':
        # Validate the form
        if not formHasMember(request.form, 'name') or request.form['name'] is None:
            flash("new restaurants must have a name")
        else:
            restaurant = Restaurant(name=request.form['name'], user_id=login_session['user_id'])

            session.add(restaurant)
            session.commit()

            flash("new restaurant %s created successfully!" % restaurant.name)
            return redirect(url_for('showRestaurants'))

    return render_template('new-restaurant.html', auth=True)

@app.route('/restaurants/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    """

    Args:
        restaurant_id: An integer value corresponding to an existing restaurant

    Returns: Responds to the user request to show the page for editing an existing restaurant and also handles the
    posted attempt at making those changes

    """
    # First, make sure the user is authenticated (cannot edit a restaurant details if not logged in)
    if not isLoggedIn():
        return redirect('/login')

    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    # Receive the attempt to edit the details for an existing restaurant or return the page for the user to do so
    if request.method == 'POST':
        # Validate the form
        if not formHasMember(request.form, 'name'):
            flash("restaurant must have a name")
        else:
            restaurant.name = request.form['name']
            restaurant.user_id = login_session['user_id']
            restaurant.updated_date = datetime.datetime.now()

            session.add(restaurant)
            session.commit()

            flash("restaurant %s successfully changed" % restaurant.name)
            return redirect(url_for('showRestaurants'))

    return render_template('edit-restaurant.html',
                           restaurant=restaurant,
                           creator=getUserInfo(restaurant.user_id),
                           auth=True)

@app.route('/restaurants/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    """

    Args:
        restaurant_id: An integer value corresponding to an existing restaurant

    Returns: Responds to the user request to show the page for deleting an existing restaurant and also handles the
    posted attempt at removing the restaurant

    """
    # First, make sure the user is authenticated (cannot remove a restaurant if not logged in)
    if not isLoggedIn():
        return redirect('/login')
    # Receive the attempt to remove the restaurant or return the page for confirming a restaurant removal
    if request.method == 'POST':
        # To prevent man-in-the-middle attacks, check for randomly generated string from the original page render
        if not formHasMember(login_session, 'nonce'):
            flash("unable to securely delete restaurant")
            return redirect('/restaurants')
        else:
            restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
            items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()

            for item in items:
                session.delete(item)

            session.commit()
            session.delete(restaurant)

            flash("restaurant %s successfully removed" % restaurant.name)
            session.commit()

            del login_session['nonce']
            return redirect(url_for('showRestaurants'))
    else:
        restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        login_session['nonce'] = generateNonce()
        return render_template('delete-restaurant.html',
                               restaurant=restaurant,
                               NONCE=login_session['nonce'],
                               auth=True)

@app.route('/restaurants/<int:restaurant_id>/', methods=['GET'])
def showMenu(restaurant_id):
    """

    Args:
        restaurant_id: An integer value corresponding to an existing restaurant

    Returns: Responds to the user request to show the page for a restaurant's menu items

    """
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if not restaurant:
        flash("Sorry, but unable to find the record for a matching restaurant")
        return redirect(url_for('showRestaurants'))

    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    if not items:
        flash("no menu items exist yet for %s" % restaurant.name)

    return render_template('menu.html',
                           restaurant=restaurant,
                           items=items,
                           creator=getUserInfo(restaurant.user_id),
                           auth=isLoggedIn())

@app.route('/restaurants/<int:restaurant_id>/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    """

    Args:
        restaurant_id: An integer value corresponding to an existing restaurant

    Returns: Responds to the user request to show the page for creating a new menu item and also handles the posted
    attempt at creating the new menu item

    """
    # First, make sure the user is authenticated (cannot create a new menu item if not logged in)
    if not isLoggedIn():
        return redirect('/login')

    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()

    # Receive the attempt to create the new menu item or return the page for the user to create one
    if request.method == 'POST':
        # Validate the form
        if not formHasMember(request.form, 'name'):
            flash("new menu items must have a name")
        else:
            newItem = MenuItem(
                name=request.form['name'],
                description=request.form['description'],
                price=request.form['price'],
                course=request.form['course'],
                restaurant_id=restaurant_id,
                user_id=login_session['user_id']
            )
            if formHasMember(request.form, 'picture'):
                newItem.picture = request.form['picture']

            session.add(newItem)
            session.commit()

            flash("new menu item %s created successfully!" % newItem.name)
            return redirect(url_for('showMenu', restaurant_id=restaurant_id))

    return render_template('new-menu-item.html', restaurant=restaurant, auth=True)

@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/edit/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    """

    Args:
        restaurant_id: An integer value corresponding to an existing restaurant
        menu_id: An integer value corresponding to an existing menu item

    Returns: Responds to the user request to show the page for editing an existing menu item and also handles the
    posted attempt at editing a menu item

    """
    # First, make sure the user is authenticated (cannot edit a menu item if not logged in)
    if not isLoggedIn():
        return redirect('/login')

    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    editItem = session.query(MenuItem).filter_by(restaurant_id=restaurant_id, id=menu_id).one()

    # Receive the attempt toe edit the menu item or return the page for the user to make any desired edits
    if request.method == 'POST':
        # Validate the form
        if not formHasMember(request.form, 'name'):
            flash("menu item must have a name")
        else:
            editItem.name = request.form['name']
            editItem.user_id = login_session['user_id']
            editItem.description = request.form['description']
            editItem.price = request.form['price']
            editItem.updated_date = datetime.datetime.now()

            if formHasMember(request.form, 'course'):
                editItem.course = request.form['course']
            if formHasMember(request.form, 'picture'):
                editItem.picture = request.form['picture']

            session.add(editItem)
            session.commit()

            flash("menu item %s successfully changed" % editItem.name)
            return redirect(url_for('showMenu', restaurant_id=restaurant_id))

    return render_template('edit-menu-item.html',
                           restaurant=restaurant,
                           item=editItem,
                           creator=getUserInfo(editItem.user_id),
                           auth=True)

@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete/', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    """

    Args:
        restaurant_id: An integer value corresponding to an existing restaurant
        menu_id: An integer value corresponding to an existing menu item

    Returns: Responds to the user request to show the page for removing an existing menu item and also handles the
    posted attempt at removing the item

    """
    # First, make sure the user is authenticated (cannot remove a menu item if not logged in)
    if not isLoggedIn():
        return redirect('/login')
    # Receive the attempt to remove the menu item or return the page for the user to remove an item
    elif request.method == 'POST':
        # To prevent man-in-the-middle attacks, check for randomly generated string from the original page render
        if not formHasMember(login_session, 'nonce'):
            flash("unable to securely delete menu item")
            return redirect('/restaurants')
        else:
            deleteItem = session.query(MenuItem).filter_by(restaurant_id=restaurant_id, id=menu_id).one()

            session.delete(deleteItem)
            flash("menu item %s successfully removed" % deleteItem.name)
            session.commit()

            del login_session['nonce']
            return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        item = session.query(MenuItem).filter_by(restaurant_id=restaurant_id, id=menu_id).one()
        login_session['nonce'] = generateNonce()
        return render_template('delete-menu-item.html',
                               restaurant=restaurant,
                               item=item,
                               NONCE=login_session['nonce'],
                               auth=True)

@app.route('/restaurants/<int:restaurant_id>/menu/JSON', methods=['GET'])
def showMenuJSON(restaurant_id):
    """

    Args:
        restaurant_id: An integer value corresponding to an existing restaurant

    Returns: A menu for a given restaurant, in JSON format

    """
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON', methods=['GET'])
def showMenuItemJSON(restaurant_id, menu_id):
    """

    Args:
        restaurant_id: An integer value corresponding to an existing restaurant
        menu_id: An integer value corresponding to an existing menu item

    Returns: An existing menu item, in JSON format

    """
    item = session.query(MenuItem).filter_by(restaurant_id=restaurant_id, id=menu_id).one()
    return jsonify(MenuItem=item.serialize)

@app.route('/restaurants/JSON', methods=['GET'])
def showRestaurantsJSON():
    """

    Returns: The list of all the existing restaurants, in JSON format

    """
    restaurants = session.query(Restaurant).all()
    return jsonify(Restaurants=[i.serialize for i in restaurants])

@app.route('/restaurants/<int:restaurant_id>/menu/atom', methods=['GET'])
def showMenuAtom(restaurant_id):
    """

    Args:
        restaurant_id: An integer value corresponding to an existing restaurant

    Returns: A menu for a given restaurant, in Atom feed format

    """
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    feed = AtomFeed('RestaurantMenu', feed_url=request.url, url=request.url_root)
    for item in items:
        author = getUserInfo(item.user_id)
        feed.add(item.name, item.name,
                 content_type='text',
                 author=author.name,
                 subtitle=item.description,
                 url=urljoin(request.url_root, "/restaurants/%s/menu/atom" % restaurant_id),
                 updated=item.updated_date,
                 published=item.created_date)
    return feed.get_response()

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/atom', methods=['GET'])
def showMenuItemAtom(restaurant_id, menu_id):
    """

    Args:
        restaurant_id: An integer value corresponding to an existing restaurant
        menu_id: An integer value corresponding to an existing menu item

    Returns: An existing menu item, in Atom feed format

    """
    item = session.query(MenuItem).filter_by(restaurant_id=restaurant_id, id=menu_id).one()
    feed = AtomFeed('MenuItem', feed_url=request.url, url=request.url_root)
    author = getUserInfo(item.user_id)
    feed.add(item.name, item.name,
             content_type='text',
             subtitle=item.description,
             author=author.name,
             url=urljoin(request.url_root, "/restaurants/%s/menu/%s/atom" % (restaurant_id, menu_id)),
             updated=item.updated_date,
             published=item.created_date)
    return feed.get_response()

@app.route('/restaurants/atom', methods=['GET'])
def showRestaurantsAtom():
    """

    Returns: The list of all the existing restaurants, in Atom feed format

    """
    restaurants = session.query(Restaurant).all()
    feed = AtomFeed('Restaurants', feed_url=request.url, url=request.url_root)
    for restaurant in restaurants:
        author = getUserInfo(restaurant.user_id)
        print author
        feed.add(restaurant.name, restaurant.name,
                 content_type='text',
                 author=author.name,
                 url=urljoin(request.url_root, '/restaurants/atom'),
                 updated=restaurant.updated_date,
                 published=restaurant.created_date)
    return feed.get_response()

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)