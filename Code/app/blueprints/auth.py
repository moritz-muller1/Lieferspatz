"""Sign-up, login and logout."""
from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db_connection
from app.storage import upload_image

bp = Blueprint('auth', __name__)


@bp.route('/signup_as')
def signup_as():
    return render_template('SignUpAs.html')


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        address = request.form.get('address', '')
        city = request.form.get('city', '')
        plz = request.form.get('plz', '')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        conn = get_db_connection()
        existing_user = conn.execute(
            'SELECT * FROM "Account" WHERE "Username" = %s', (username,)).fetchone()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('auth.signup'))

        conn.execute(
            'INSERT INTO "Customer" ("Username", "FirstName", "LastName", "Address", "City", "PLZ")'
            ' VALUES (%s, %s, %s, %s, %s, %s)',
            (username, first_name, last_name, address, city, plz))
        conn.execute(
            'INSERT INTO "Account" ("Username", "Password", "UserType") VALUES (%s, %s, %s)',
            (username, hashed_password, 'Customer'))
        conn.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('SignUp.html')


@bp.route('/signup_restaurant', methods=['GET', 'POST'])
def signup_restaurant():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        address = request.form['address']
        plz = request.form['plz']
        city = request.form['city']
        description = request.form['description']

        picture_url = upload_image(request.files.get('picture'),
                                   public_id=f'restaurant_{username}')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        conn = get_db_connection()
        existing_user = conn.execute(
            'SELECT * FROM "Account" WHERE "Username" = %s', (username,)).fetchone()
        if existing_user:
            flash('Username already exists', 'error')
            return redirect(url_for('auth.login'))

        conn.execute(
            'INSERT INTO "Restaurant" ("Username", "FirstName", "LastName", "Address", "PLZ", "City", "Description", "Picture") '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
            (username, first_name, last_name, address, plz, city, description, picture_url))
        conn.execute(
            'INSERT INTO "Account" ("Username", "Password", "UserType") VALUES (%s, %s, %s)',
            (username, hashed_password, 'Restaurant'))
        conn.commit()

        flash('Restaurant account created successfully!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('SignUpRestaurant.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        account_info = conn.execute(
            'SELECT "Username", "Password", "UserType" FROM "Account" WHERE "Username" = %s',
            (username,)).fetchone()

        if account_info:
            if check_password_hash(account_info['Password'] or '', password):
                session.clear()
                session['username'] = username
                session['user_type'] = account_info['UserType']

                if account_info['UserType'] == 'Customer':
                    customer_info = conn.execute(
                        'SELECT "CustomerID" FROM "Customer" WHERE "Username" = %s',
                        (username,)).fetchone()
                    if customer_info:
                        session['user_id'] = customer_info['CustomerID']
                elif account_info['UserType'] == 'Restaurant':
                    restaurant_info = conn.execute(
                        'SELECT "RestaurantID" FROM "Restaurant" WHERE "Username" = %s',
                        (username,)).fetchone()
                    if restaurant_info:
                        session['user_id'] = restaurant_info['RestaurantID']
                        session['restaurant_id'] = restaurant_info['RestaurantID']

                flash('Logged in successfully!', 'success')
                return redirect(url_for('restaurant.dashboard')) if session['user_type'] == 'Restaurant' \
                    else redirect(url_for('customer.show_restaurants'))
            else:
                flash('Invalid username or password.', 'error')
        else:
            flash('Invalid username or password.', 'error')

    return render_template('Login.html')


@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))
