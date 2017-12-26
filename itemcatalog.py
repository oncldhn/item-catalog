import urllib2

from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy.orm import sessionmaker
from flask import session as login_session
import json
import random
import string
import requests
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2

from database_setup import *
from flask import make_response


app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web'][
    'client_id']
APPLICATION_NAME = "Item Catalog Application"
app.secret_key = 'super_secret_key'
engine = create_engine('sqlite:///itemcatalog.db')
googleTokenURL = 'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token'\
                 '=%s'
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Page routings
@app.route('/login')
def showLoginPage():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', user=login_session.get('username'),
                           STATE=state)


# authenticates google sign in request
@app.route('/gconnect', methods=['POST'])
def gconnect():
    client_state = request.args.get('state')
    print client_state
    print login_session['state']
    if not login_session['state'] == client_state:
        response = make_response(json.dumps('Invalid state'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # Obtain authorization code
        code = request.data

        try:
            # Upgrade the authorization code into a credentials object
            oauth_flow = flow_from_clientsecrets('client_secrets.json',
                                                 scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(code)
        except FlowExchangeError:
            response = make_response(
                json.dumps('Failed to upgrade the authorization code.'), 402)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Check that the access token is valid.
        access_token = credentials.access_token
        url = (googleTokenURL % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Verify that the access token is used for the intended user.
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            response = make_response(
                json.dumps("Token's user ID doesn't match given user ID."),
                401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Get user info
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)

        data = answer.json()

        # Store the access token in the session for later use.
        login_session['id_token'] = code
        login_session['username'] = data['name']
        login_session['email'] = data['email']

        if not getUserID(login_session['email']):
            new_user = User(name=login_session['username'],
                            email=login_session['email'])
            session.add(new_user)
            session.commit()
        return "success"


# disconnects user
@app.route('/gdisconnect/')
def gdisconnect():
    id_token = login_session.get('id_token')
    if id_token:
        # Clear session
        del login_session['id_token']
        del login_session['username']
        del login_session['email']

    return redirect(url_for('showCategories'))


@app.route('/')
def showCategories():
    categories = session.query(Category).all()
    return render_template('categories.html',
                           user=login_session.get('username'),
                           categories=categories)


@app.route('/category/<int:category_id>/')
def showCategory(category_id):
    categories = session.query(Category).all()
    category = session.query(Category).filter(
               Category.id == category_id).first()
    return render_template('items.html',
                           user=login_session.get('username'),
                           categories=categories,
                           selectedCategory=category)


@app.route('/item/<int:item_id>/')
def showItem(item_id):
    item = session.query(Item).filter(Item.id == item_id).first()
    categories = session.query(Category).all()
    category = session.query(Category).filter(
        Category.id == item.category_id).first()
    user_id = getUserID(login_session.get('email'))

    return render_template('item.html', user_id=user_id,
                           user=login_session.get('username'),
                           categories=categories,
                           selectedCategory=category,
                           selectedItem=item)


@app.route('/additem/', methods=['GET', 'POST'])
def addItem():
    if request.method == 'GET':
        # show add item form
        user = login_session.get('username')
        categories = session.query(Category).all()
        return render_template('addItem.html',
                               categories=categories, user=user)
    else:
        # insert item
        category = int(request.values.get('category'))
        name = request.values.get('name')
        description = request.values.get('description')
        user_id = getUserID(login_session.get('email'))
        if not user_id:
            response = make_response('Illegal access', 401)
            return response

        item = Item(name=name, description=description, category_id=category,
                    user_id=user_id)
        session.add(item)
        session.commit()

        return redirect(url_for('showItem', item_id=item.id))


@app.route('/editItem/<int:item_id>/', methods=['GET', 'POST'])
def editItem(item_id):
    if request.method == 'GET':
        # show item values
        user_id = getUserID(login_session.get('email'))
        categories = session.query(Category).all()
        item = session.query(Item).filter(Item.id == item_id).first()
        return render_template('addItem.html', categories=categories,
                               user=user_id, item=item)
    else:
        # Update item values
        category = int(request.values.get('category'))
        name = request.values.get('name')
        description = request.values.get('description')
        client_state = request.args.get('state')
        user_id = getUserID(login_session.get('email'))
        item = session.query(Item).filter(Item.id == item_id).first()

        if not user_id or user_id != item.user_id:
            response = make_response('Unauthorized', 401)
            return response

        item.name = name
        item.description = description
        item.category_id = category

        session.commit()

        return redirect(url_for('showItem', item_id=item.id))


@app.route('/deleteItem/<int:item_id>/', methods=['POST'])
def deleteItem(item_id):
    user_id = getUserID(login_session.get('email'))
    item = session.query(Item).filter(Item.id == item_id).first()

    if not user_id or user_id != item.user_id:
        response = make_response('Unauthorized', 401)
        return response

    session.delete(item)
    session.commit()

    return redirect(url_for('showCategory', category_id=item.category_id))


# Json Api
@app.route('/categories/json/')
def categories():
    categories = session.query(Category).all()
    return jsonify(categories=[category.serialize for category in categories])


@app.route('/category/<int:category_id>/items/json/')
def items(category_id):
    items = session.query(Item).filter(Item.category_id == category_id).all()
    return jsonify(items=[item.serialize for item in items])


# utility methods
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    user = session.query(User).filter(
        User.email == email).first()
    if user:
        return user.id
    else:
        return None


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
