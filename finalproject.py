from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem
from pprint import pprint
app = Flask(__name__)

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

courses = [{'id':1,'name':'Appetizer'}, {'id':2,'name':'Entree'}, {'id':3,'name':'Dessert'}, {'id':4,'name':'Beverage'}]

@app.route('/')
@app.route('/restaurants/')
def showRestaurants():
    #restaurants = session.query(Restaurant).order_by(func.lower(Restaurant.name)).all()
    stmt = session.query(MenuItem, func.count('*').label('item_count')).group_by(MenuItem.restaurant_id).subquery()
    restaurants = session.query(Restaurant, stmt.c.item_count).outerjoin(stmt, stmt.c.restaurant_id == Restaurant.id).order_by(func.lower(Restaurant.name)).group_by(Restaurant.name).all()
    return render_template('restaurants.html', restaurants = restaurants)

@app.route('/restaurant/new/', methods = ['GET','POST'])
def newRestaurant():
    if request.method == 'POST':
        newRestaurant = Restaurant(name = request.form['name'])
        session.add(newRestaurant)
        session.commit()
        flash('New restaurant added!')
        return redirect(url_for('showRestaurants'))
    if request.method == 'GET':
        return render_template('newrestaurant.html')

@app.route('/restaurant/<int:restaurant_id>/edit/', methods = ['GET','POST'])
def editRestaurant(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    return render_template('editrestaurant.html', restaurant = restaurant)

@app.route('/restaurant/<int:restaurant_id>/delete/', methods = ['GET','POST'])
def deleteRestaurant(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
        session.delete(restaurant)
        session.commit()
        flash('Restaurant deleted!')
        return redirect(url_for('showRestaurants'))
    if request.method == 'GET':
        return render_template('deleterestaurant.html', restaurant = restaurant)

@app.route('/restaurant/<int:restaurant_id>')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    # to do (in future): change course to enum
    try:
        restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
        items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).order_by(MenuItem.course, MenuItem.name).all()
        return render_template('menu.html', restaurant = restaurant, items = items)
    except:
        flash('Restaurant not found')
        return redirect(url_for('showRestaurants'))

@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods = ['GET','POST'])
def newMenuItem(restaurant_id):
    if request.method == 'POST':
        form = request.form
        newItem = MenuItem(name = form['name'],
                           description = form['description'],
                           price = form['price'],
                           course = form['course'],
                           restaurant_id = restaurant_id)
        session.add(newItem)
        session.commit()
        flash('Menu item created!')
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    if request.method == 'GET':
        return render_template('newmenuitem.html', restaurant_id = restaurant_id, courses = courses)

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit/', methods = ['GET','POST'])
def editMenuItem(restaurant_id, menu_id):
    item = session.query(MenuItem).filter_by(id = menu_id).one()
    if request.method == 'POST':
        form = request.form
        item.name = form['name']
        item.description = form['description']
        item.price = form['price']
        item.course = form['course']
        session.commit()
        flash('Menu item edited!')
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    if request.method == 'GET':
        return render_template('editmenuitem.html', item = item, courses = courses)

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete/', methods = ['GET','POST'])
def deleteMenuItem(restaurant_id, menu_id):
    item = session.query(MenuItem).filter_by(id = menu_id).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    if request.method == 'POST':
        return render_template('deletemenuitem.html', item = item)

@app.route('/restaurants/json/')
def getRestaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify({'Restaurants':[restaurant.serialize for restaurant in restaurants]})

@app.route('/restaurant/<int:restaurant_id>/menu/json/')
def getMenuJSON(restaurant_id):
    try:
        restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
        menu = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
        return jsonify({'id':restaurant_id, 'name':restaurant.name, 'menuItems':[item.serialize for item in menu]})
    except:
        return 'Restaurant not found'

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/json/')
def getMenuItemJSON(restaurant_id, menu_id):
    try:
        item = session.query(MenuItem).filter_by(id = menu_id, restaurant_id = restaurant_id).one()
        return jsonify({'MenuItem':item.serialize})
    except:
        return 'Item not found'


if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
