"""Restaurant management: dashboard, menu, delivery areas and order handling."""
from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for
)

from app.db import DBError, get_db_connection

bp = Blueprint('restaurant', __name__)


def get_restaurant_info(username):
    if session.get('user_type') != 'Restaurant':
        return None
    conn = get_db_connection()
    return conn.execute(
        'SELECT * FROM "Restaurant" WHERE "Username" = %s', (username,)).fetchone()


@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('You need to login first.', 'info')
        return redirect(url_for('auth.login'))

    if session.get('user_type') == 'Restaurant':
        conn = get_db_connection()
        restaurant_info = conn.execute(
            'SELECT * FROM "Restaurant" WHERE "Username" = %s', (session['username'],)).fetchone()
        if restaurant_info:
            return render_template('Dashboard.html', restaurant=restaurant_info)
        flash('Restaurant not found.', 'error')
        return redirect(url_for('main.home'))

    flash('Access denied. This area is for restaurant managers only.', 'error')
    return redirect(url_for('main.home'))


@bp.route('/manage_restaurant', methods=['GET', 'POST'])
def manage_restaurant():
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        flash('You must be logged in as a restaurant to access this page.', 'error')
        return redirect(url_for('auth.login'))

    restaurant_id = session.get('restaurant_id')
    restaurant_info = None
    postal_codes = []

    conn = get_db_connection()
    try:
        restaurant_info = conn.execute(
            'SELECT * FROM "Restaurant" WHERE "RestaurantID" = %s', (restaurant_id,)).fetchone()
        postal_codes = conn.execute(
            'SELECT "Code" FROM "Codes" WHERE "RestaurantID" = %s', (restaurant_id,)).fetchall()
    except DBError as e:
        flash('An error occurred while retrieving restaurant information.', 'error')
        print(e)

    return render_template('ManageRestaurant.html',
                           restaurant_info=restaurant_info,
                           postal_codes=postal_codes)


@bp.route('/update_hours/<int:restaurant_id>', methods=['POST'])
def update_hours(restaurant_id):
    if 'user_id' not in session or session.get('restaurant_id') != restaurant_id:
        flash('Access denied.', 'error')
        return redirect(url_for('auth.login'))

    opening_time = request.form['opening_time']
    closing_time = request.form['closing_time']

    conn = get_db_connection()
    try:
        conn.execute(
            'UPDATE "Restaurant" SET "OpeningTime" = %s, "ClosingTime" = %s WHERE "RestaurantID" = %s',
            (opening_time, closing_time, restaurant_id))
        conn.commit()
        flash('Hours updated successfully!', 'success')
    except DBError as e:
        conn.rollback()
        flash('Failed to update hours.', 'error')
        print(e)

    return redirect(url_for('restaurant.manage_restaurant'))


@bp.route('/add_code/<int:restaurant_id>', methods=['POST'])
def add_code(restaurant_id):
    if 'user_id' not in session or session.get('restaurant_id') != restaurant_id:
        flash('Access denied.', 'error')
        return redirect(url_for('auth.login'))

    new_code = request.form['code']
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO "Codes" ("RestaurantID", "Code") VALUES (%s, %s)',
                     (restaurant_id, new_code))
        conn.commit()
        flash('Postal code added successfully!', 'success')
    except DBError as e:
        conn.rollback()
        flash('Failed to add postal code.', 'error')
        print(e)

    return redirect(url_for('restaurant.manage_restaurant'))


@bp.route('/delete_code/<int:restaurant_id>/<code>', methods=['POST'])
def delete_code(restaurant_id, code):
    if 'user_id' not in session or session.get('restaurant_id') != restaurant_id:
        flash('Access denied.', 'error')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM "Codes" WHERE "RestaurantID" = %s AND "Code" = %s',
                     (restaurant_id, code))
        conn.commit()
        flash('Postal code removed successfully!', 'success')
    except DBError as e:
        conn.rollback()
        flash('Failed to remove postal code.', 'error')
        print(e)

    return redirect(url_for('restaurant.manage_restaurant'))


@bp.route('/manage_menu')
def manage_menu():
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('auth.login'))

    restaurant_id = session['user_id']
    conn = get_db_connection()
    menu_items = conn.execute(
        'SELECT * FROM "MenuItem" WHERE "RestaurantID" = %s', (restaurant_id,)).fetchall()
    return render_template('ManageMenu.html', menu_items=menu_items)


@bp.route('/edit_menu_item/<int:item_id>', methods=['GET', 'POST'])
def edit_menu_item(item_id):
    if 'user_id' not in session:
        flash('Please login to access this page.', 'warning')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form.get('name', '')
        price = request.form.get('price', '')
        description = request.form.get('description', '')

        if not (name and price and description):
            flash('Please provide all required fields.', 'error')
            return redirect(url_for('restaurant.edit_menu_item', item_id=item_id))

        conn.execute(
            'UPDATE "MenuItem" SET "Name" = %s, "Price" = %s, "Description" = %s WHERE "MenuItemID" = %s',
            (name, price, description, item_id))
        conn.commit()
        flash('Menu item updated successfully!', 'success')
        return redirect(url_for('restaurant.manage_menu'))

    item = conn.execute(
        'SELECT * FROM "MenuItem" WHERE "MenuItemID" = %s', (item_id,)).fetchone()
    if item is None:
        flash('Menu item not found.', 'error')
        return redirect(url_for('restaurant.manage_menu'))
    return render_template('EditMenuItem.html', item=item)


@bp.route('/delete_menu_item/<int:item_id>', methods=['POST'])
def delete_menu_item(item_id):
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        flash('You need to be logged in as a restaurant to perform this action.', 'error')
        return redirect(url_for('auth.login'))

    restaurant_id = session['user_id']

    conn = get_db_connection()
    try:
        restaurant = conn.execute(
            'SELECT "RestaurantID" FROM "Restaurant" WHERE "RestaurantID" = %s',
            (restaurant_id,)).fetchone()
        if restaurant:
            conn.execute('DELETE FROM "MenuItem" WHERE "MenuItemID" = %s AND "RestaurantID" = %s',
                         (item_id, restaurant['RestaurantID']))
            conn.commit()
            flash('Menu item deleted successfully.', 'success')
        else:
            flash('Restaurant not found.', 'error')
    except DBError as e:
        conn.rollback()
        flash('An error occurred. Please try again.', 'error')
        print(e)

    return redirect(url_for('restaurant.manage_menu'))


@bp.route('/add_menu_item', methods=['GET', 'POST'])
def add_menu_item():
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        flash('You need to be logged in as a restaurant to perform this action.', 'error')
        return redirect(url_for('auth.login'))

    restaurant_id = session['user_id']

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        price = request.form['price']

        conn = get_db_connection()
        try:
            restaurant = conn.execute(
                'SELECT "RestaurantID" FROM "Restaurant" WHERE "RestaurantID" = %s',
                (restaurant_id,)).fetchone()
            if restaurant:
                conn.execute(
                    'INSERT INTO "MenuItem" ("RestaurantID", "Name", "Description", "Category", "Price") '
                    'VALUES (%s, %s, %s, %s, %s)',
                    (restaurant['RestaurantID'], name, description, category, price))
                conn.commit()
                flash('New menu item added successfully.', 'success')
            else:
                flash('Restaurant not found.', 'error')
        except DBError as e:
            conn.rollback()
            flash('An error occurred. Please try again.', 'error')
            print(e)

        return redirect(url_for('restaurant.manage_menu'))

    return render_template('AddMenuItem.html')


@bp.route('/view_orders')
def view_orders():
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        flash('Access denied. Please log in as a restaurant.', 'error')
        return redirect(url_for('auth.login'))

    restaurant_id = session.get('restaurant_id')
    if not restaurant_id:
        flash('Restaurant ID not found in session. Please log in again.', 'error')
        return redirect(url_for('auth.login'))

    return render_template(
        'ViewOrders.html',
        pending_orders=_orders_by_status(restaurant_id, 'Pending'),
        ongoing_orders=_orders_by_status(restaurant_id, 'Processing'),
        completed_orders=_orders_by_status(restaurant_id, 'Delivered'),
    )


def _orders_by_status(restaurant_id, status):
    conn = get_db_connection()
    return conn.execute(
        'SELECT * FROM "OrderTable" WHERE "Status" = %s AND "ReceivedBy" = %s',
        (status, restaurant_id)).fetchall()


@bp.route('/accept_order/<int:order_id>', methods=['POST'])
def accept_order(order_id):
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE \"OrderTable\" SET \"Status\" = 'Processing' "
            "WHERE \"OrderID\" = %s AND \"Status\" = 'Pending'", (order_id,))
        conn.commit()
        flash('Order has been accepted and is now processing.', 'success')
    except DBError as e:
        conn.rollback()
        flash('An error occurred while updating the order status.', 'error')
        print(e)

    return redirect(url_for('restaurant.view_orders'))


@bp.route('/mark_as_delivered/<int:order_id>', methods=['POST'])
def mark_as_delivered(order_id):
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE \"OrderTable\" SET \"Status\" = 'Delivered' "
            "WHERE \"OrderID\" = %s AND \"Status\" = 'Processing'", (order_id,))
        conn.commit()
        flash('Order has been marked as delivered.', 'success')
    except DBError as e:
        conn.rollback()
        flash('An error occurred while updating the order status.', 'error')
        print(e)

    return redirect(url_for('restaurant.view_orders'))


@bp.route('/reject_order/<int:order_id>', methods=['POST'])
def reject_order(order_id):
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE \"OrderTable\" SET \"Status\" = 'Cancelled' WHERE \"OrderID\" = %s", (order_id,))
        conn.commit()
        flash('Order has been cancelled.', 'success')
    except DBError as e:
        conn.rollback()
        flash('An error occurred while cancelling the order.', 'error')
        print(e)

    return redirect(url_for('restaurant.view_orders'))


@bp.route('/order_details/<int:order_id>')
def order_details(order_id):
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    order_info = conn.execute('''
        SELECT ot."OrderID", ot."SubmissionTime",
               c."FirstName" || ' ' || c."LastName" AS "CustomerName",
               c."Address", c."City", c."PLZ"
        FROM "OrderTable" ot
        LEFT JOIN "Customer" c ON ot."ReviewedBy" = c."CustomerID"
        WHERE ot."OrderID" = %s
    ''', (order_id,)).fetchone()

    if not order_info:
        flash('Order not found.', 'error')
        return redirect(url_for('main.home'))

    items_ordered = conn.execute('''
        SELECT mi."Name", mi."Description", mi."Price", od."Quantity"
        FROM "OrderDetails" od
        INNER JOIN "MenuItem" mi ON od."ItemID" = mi."MenuItemID"
        WHERE od."OrderID" = %s
    ''', (order_id,)).fetchall()

    total_price = sum(item['Price'] * item['Quantity'] for item in items_ordered)

    return render_template('OrderDetails.html', order_info=order_info,
                           items_ordered=items_ordered, total_price=total_price)
