"""Customer-facing flows: browsing restaurants, cart and orders."""
from datetime import datetime

from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for
)

from app.db import DBError, get_db_connection

bp = Blueprint('customer', __name__)


@bp.route('/restaurants')
def show_restaurants():
    customer_id = session.get('user_id')
    if not customer_id:
        flash('You must be logged in to view restaurants.', 'error')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    try:
        customer_info = conn.execute(
            'SELECT "PLZ" FROM "Customer" WHERE "CustomerID" = %s', (customer_id,)).fetchone()
        if customer_info:
            customer_postal_code = customer_info['PLZ']
        else:
            flash('Customer information not found.', 'error')
            return redirect(url_for('main.home'))

        current_time = datetime.now().strftime('%H:%M')

        restaurants = conn.execute("""
            SELECT DISTINCT r.* FROM "Restaurant" r
            INNER JOIN "Codes" c ON r."RestaurantID" = c."RestaurantID"
            WHERE c."Code" = %s AND
                  r."OpeningTime" <= %s AND
                  r."ClosingTime" > %s
        """, (customer_postal_code, current_time, current_time)).fetchall()
    except DBError as e:
        flash('An error occurred while retrieving restaurant information.', 'error')
        print(e)
        restaurants = []

    return render_template('Res-Overview.html', restaurants=restaurants)


@bp.route('/menu/<int:restaurant_id>')
def show_menu(restaurant_id):
    conn = get_db_connection()
    menu_items = conn.execute(
        'SELECT * FROM "MenuItem" WHERE "RestaurantID" = %s', (restaurant_id,)).fetchall()
    return render_template('Menu.html', menu_items=menu_items, restaurant_id=restaurant_id)


@bp.route('/add_to_cart/<int:restaurant_id>/<int:menu_item_id>', methods=['POST'])
def add_to_cart(restaurant_id, menu_item_id):
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('auth.login'))

    quantity = request.form['quantity']
    customer_id = session['user_id']

    conn = get_db_connection()
    try:
        cart_item = conn.execute(
            'SELECT * FROM "Cart" WHERE "CustomerID" = %s AND "ItemID" = %s',
            (customer_id, menu_item_id)).fetchone()

        if cart_item:
            new_quantity = cart_item['Quantity'] + int(quantity)
            conn.execute('UPDATE "Cart" SET "Quantity" = %s WHERE "CartID" = %s',
                         (new_quantity, cart_item['CartID']))
        else:
            conn.execute('INSERT INTO "Cart" ("CustomerID", "ItemID", "Quantity") VALUES (%s, %s, %s)',
                         (customer_id, menu_item_id, quantity))

        conn.commit()
        flash('Item added to cart', 'success')
    except DBError:
        conn.rollback()
        flash('Database error occurred. Please try again.')

    return redirect(url_for('customer.show_menu', restaurant_id=restaurant_id))


@bp.route('/update_cart/<int:cart_item_id>', methods=['POST'])
def update_cart(cart_item_id):
    new_quantity = request.form['quantity']
    if int(new_quantity) > 0:
        conn = get_db_connection()
        conn.execute('UPDATE "Cart" SET "Quantity" = %s WHERE "CartID" = %s',
                     (new_quantity, cart_item_id))
        conn.commit()
        flash('Cart updated successfully!', 'success')
    else:
        return redirect(url_for('customer.remove_from_cart', cart_item_id=cart_item_id))
    return redirect(url_for('customer.view_cart'))


@bp.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
def remove_from_cart(cart_item_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM "Cart" WHERE "CartID" = %s', (cart_item_id,))
    conn.commit()
    flash('Item removed from cart', 'success')
    return redirect(url_for('customer.view_cart'))


@bp.route('/cart')
def view_cart():
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('auth.login'))

    customer_id = session['user_id']
    conn = get_db_connection()
    cart_items = conn.execute(
        '''SELECT "Cart"."CartID", "MenuItem"."Name", "MenuItem"."Description",
                  "MenuItem"."Price", "Cart"."Quantity"
           FROM "Cart"
           JOIN "MenuItem" ON "Cart"."ItemID" = "MenuItem"."MenuItemID"
           WHERE "Cart"."CustomerID" = %s''', (customer_id,)).fetchall()
    total_price = sum(item['Price'] * item['Quantity'] for item in cart_items)
    return render_template('Cart.html', cart_items=cart_items, total_price=total_price)


@bp.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('auth.login'))

    customer_id = session['user_id']
    conn = get_db_connection()
    order_id = None

    try:
        cart_item = conn.execute('''
            SELECT "ItemID", "RestaurantID" FROM "Cart"
            JOIN "MenuItem" ON "Cart"."ItemID" = "MenuItem"."MenuItemID"
            WHERE "Cart"."CustomerID" = %s LIMIT 1
        ''', (customer_id,)).fetchone()

        if cart_item:
            restaurant_id = cart_item['RestaurantID']

            row = conn.execute('''
                INSERT INTO "OrderTable" ("ReviewedBy", "ReceivedBy", "Status", "SubmissionTime")
                VALUES (%s, %s, 'Pending', CURRENT_TIMESTAMP)
                RETURNING "OrderID"
            ''', (customer_id, restaurant_id)).fetchone()
            order_id = row['OrderID']

            cart_items = conn.execute('''
                SELECT "CartID", "ItemID", "Quantity",
                       ("MenuItem"."Price" * "Cart"."Quantity") AS "TotalPrice"
                FROM "Cart" JOIN "MenuItem" ON "Cart"."ItemID" = "MenuItem"."MenuItemID"
                WHERE "Cart"."CustomerID" = %s
            ''', (customer_id,)).fetchall()

            for item in cart_items:
                conn.execute('''
                    INSERT INTO "OrderDetails" ("OrderID", "ItemID", "Quantity", "TotalPrice")
                    VALUES (%s, %s, %s, %s)
                ''', (order_id, item['ItemID'], item['Quantity'], item['TotalPrice']))
                conn.execute('''
                    INSERT INTO "Checkout" ("CartID", "OrderID") VALUES (%s, %s)
                ''', (item['CartID'], order_id))

            conn.execute('DELETE FROM "Cart" WHERE "CustomerID" = %s', (customer_id,))

            conn.commit()
            flash('Order placed successfully!', 'success')
        else:
            flash('Your cart is empty.', 'error')
            conn.rollback()

    except DBError as e:
        conn.rollback()
        order_id = None
        flash('An error occurred while placing the order. Please try again.', 'error')
        print(e)

    if order_id:
        return redirect(url_for('customer.track_order', order_id=order_id))
    return redirect(url_for('customer.view_cart'))


@bp.route('/track_order/<int:order_id>')
def track_order(order_id):
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    order_row = conn.execute(
        'SELECT * FROM "OrderTable" WHERE "OrderID" = %s', (order_id,)).fetchone()

    if order_row is None:
        flash('Order not found.', 'error')
        return redirect(url_for('main.home'))

    order = dict(order_row)

    submitted = order.get('SubmissionTime')
    if isinstance(submitted, str):
        order['SubmissionTime'] = datetime.strptime(submitted, '%Y-%m-%d %H:%M:%S')

    status_width = "0%"
    if order['Status'] == 'Pending':
        status_width = "25%"
    elif order['Status'] == 'Processing':
        status_width = "50%"
    elif order['Status'] in ('Delivered', 'Cancelled'):
        status_width = "100%"

    return render_template('TrackingOrder.html', order=order, status_width=status_width)


@bp.route('/order_history')
def order_history():
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('auth.login'))

    customer_id = session['user_id']
    conn = get_db_connection()
    try:
        orders = conn.execute('''
            SELECT ot."OrderID", ot."Status", ot."SubmissionTime",
                   r."FirstName" || ' ' || r."LastName" AS "RestaurantName"
            FROM "OrderTable" ot
            JOIN "Restaurant" r ON ot."ReceivedBy" = r."RestaurantID"
            WHERE ot."ReviewedBy" = %s
        ''', (customer_id,)).fetchall()
        if not orders:
            flash('No orders found.')
        return render_template('OrderHistory.html', orders=orders)
    except DBError as e:
        flash('An error occurred while retrieving the order history. Please try again.')
        print(e)
        return redirect(url_for('main.home'))
