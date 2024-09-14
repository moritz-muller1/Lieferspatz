from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
import os

#Add a configuration for the upload folder and allowed extensions
app = Flask(__name__)
app.secret_key = 'magdykobry'
app.config['UPLOAD_FOLDER'] = 'static/images'  # Make sure this path exists and is correct
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']



# Database connection
def get_db_connection():
    conn = sqlite3.connect('C:/Users/M7MDKAN/Documents/UDE/5.Semester/Datenbanken Praktikum/Code/Project-FinalDB.db')
    conn.row_factory = sqlite3.Row
    return conn



@app.route('/')
def home():
    return render_template('HomePage.html')


@app.route('/signup_as')
def signup_as():
    return render_template('SignUpAs.html')


@app.route('/signup', methods=['GET', 'POST'])
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
        existing_user = conn.execute('SELECT * FROM Account WHERE Username = ?', (username,)).fetchone()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('auth.signup'))

        conn.execute('INSERT INTO Customer (Username, FirstName, LastName, Address, City, PLZ)'
                     ' VALUES (?, ?, ?, ?, ?, ?)',
                     (username, first_name, last_name, address, city, plz))
        conn.execute('INSERT INTO Account (Username, Password, UserType) VALUES (?, ?, ?)',
                     (username, hashed_password, 'Customer'))
        conn.commit()
        conn.close()

        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('SignUp.html')


@app.route('/signup_restaurant', methods=['GET', 'POST'])
def signup_restaurant():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        address = request.form['address']
        plz = request.form['plz']
        city = request.form['city']
        description = request.form['description']
        picture = request.files['picture']
        if picture and allowed_file(picture.filename):
            # Here's where we change the filename to the username with .jpg extension
            filename = secure_filename(username + '.jpg')
            picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            picture.save(picture_path)

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM Account WHERE Username = ?', (username,)).fetchone()
        if existing_user:
            flash('Username already exists','error')
            return redirect(url_for('login'))

        # Insert into the Restaurant table and Account table
        conn.execute('INSERT INTO Restaurant (Username, FirstName, LastName, Address, PLZ, City, Description, Picture) '
                     'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (username, first_name, last_name, address, plz, city, description, r"C:\Users\Mohammed Jamal\Desktop\code 2\Code\static\images"))
        # Optional: Handle picture filename if uploading files
        conn.execute('INSERT INTO Account (Username, Password, UserType) VALUES (?, ?, ?)',
                     (username, hashed_password, 'Restaurant'))
        conn.commit()
        conn.close()

        flash('Restaurant account created successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('SignUpRestaurant.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        account_info = conn.execute(
            'SELECT Username, Password, UserType FROM Account WHERE Username = ?', (username,)).fetchone()

        if account_info:
            # Check password (supports both hashed and plain text)
            password_matches = account_info['Password'].startswith('pbkdf2:sha256:') and \
                               check_password_hash(account_info['Password'], password) or \
                               not account_info['Password'].startswith('pbkdf2:sha256:') and \
                               account_info['Password'] == password

            if password_matches:
                session.clear()
                session['username'] = username
                session['user_type'] = account_info['UserType']

                if account_info['UserType'] == 'Customer':
                    customer_info = conn.execute(
                        'SELECT CustomerID FROM Customer WHERE Username = ?', (username,)).fetchone()
                    if customer_info:
                        session['user_id'] = customer_info['CustomerID']
                elif account_info['UserType'] == 'Restaurant':
                    restaurant_info = conn.execute(
                        'SELECT RestaurantID FROM Restaurant WHERE Username = ?', (username,)).fetchone()
                    if restaurant_info:
                        session['user_id'] = restaurant_info['RestaurantID']
                        session['restaurant_id'] = restaurant_info['RestaurantID']  # Set the restaurant_id in session

                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard')) if session['user_type'] == 'Restaurant' \
                    else redirect(url_for('show_restaurants'))
            else:
                flash('Invalid username or password.', 'error')
        else:
            flash('Invalid username or password.', 'error')

        conn.close()
    return render_template('Login.html')


@app.route('/logout')
def logout():
    session.clear()  # This clears all data in the session
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/restaurants')
def show_restaurants():
    # Retrieve the customer_id from the session
    customer_id = session['user_id']

    # If there is no customer_id in the session, redirect to login or some other appropriate action
    if not customer_id:
        flash('You must be logged in to view restaurants.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        # Retrieve the customer's postal code from the Customer table using customer_id
        customer_info = conn.execute('SELECT PLZ FROM Customer WHERE CustomerID = ?', (customer_id,)).fetchone()
        if customer_info:
            customer_postal_code = customer_info['PLZ']
        else:
            flash('Customer information not found.', 'error')
            return redirect(url_for('some_page'))  # Redirect to a relevant page

        # Get the current time in the appropriate format (HH:MM)
        current_time = datetime.now().strftime('%H:%M')

        # Query to select restaurants that are currently open and deliver to the customer's postal code
        restaurants = conn.execute("""
            SELECT DISTINCT r.* FROM Restaurant r
            INNER JOIN Codes c ON r.RestaurantID = c.RestaurantID
            WHERE c.Code = ? AND
                  r.OpeningTime <= ? AND
                  r.ClosingTime > ?
        """, (customer_postal_code, current_time, current_time)).fetchall()
    except sqlite3.Error as e:
        flash('An error occurred while retrieving restaurant information.', 'error')
        print(e)
        restaurants = []  # Default to an empty list in case of an error
    finally:
        conn.close()

    return render_template('Res-Overview.html', restaurants=restaurants)


@app.route('/menu/<int:restaurant_id>')
def show_menu(restaurant_id):
    conn = get_db_connection()
    menu_items = conn.execute('SELECT * FROM MenuItem WHERE RestaurantID = ?', (restaurant_id,)).fetchall()
    conn.close()
    return render_template('Menu.html', menu_items=menu_items, restaurant_id=restaurant_id)


@app.route('/add_to_cart/<int:restaurant_id>/<int:menu_item_id>', methods=['POST'])
def add_to_cart(restaurant_id, menu_item_id):
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('login'))

    quantity = request.form['quantity']
    customer_id = session['user_id']

    conn = get_db_connection()
    try:
        cart_item = conn.execute(
            'SELECT * FROM Cart WHERE CustomerID = ? AND ItemID = ?',
            (customer_id, menu_item_id)).fetchone()

        if cart_item:
            new_quantity = cart_item['Quantity'] + int(quantity)
            conn.execute('UPDATE Cart SET Quantity = ? WHERE CartID = ?', (new_quantity, cart_item['CartID']))
        else:
            conn.execute('INSERT INTO Cart (CustomerID, ItemID, Quantity) VALUES (?, ?, ?)',
                         (customer_id, menu_item_id, quantity))

        conn.commit()
        flash('Item added to cart', 'success')
    except sqlite3.Error:
        flash('Database error occurred. Please try again.')
    finally:
        conn.close()

    return redirect(url_for('show_menu', restaurant_id=restaurant_id))


@app.route('/update_cart/<int:cart_item_id>', methods=['POST'])
def update_cart(cart_item_id):
    new_quantity = request.form['quantity']
    if int(new_quantity) > 0:
        conn = get_db_connection()
        conn.execute('UPDATE Cart SET Quantity = ? WHERE CartID = ?', (new_quantity, cart_item_id))
        conn.commit()
        conn.close()
        flash('Cart updated successfully!', 'success')
    else:
        # Assuming a quantity of 0 should remove the item
        return redirect(url_for('remove_from_cart', cart_item_id=cart_item_id))
    return redirect(url_for('view_cart'))


@app.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
def remove_from_cart(cart_item_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Cart WHERE CartID = ?', (cart_item_id,))
    conn.commit()
    conn.close()
    flash('Item removed from cart', 'success')
    return redirect(url_for('view_cart'))


@app.route('/cart')
def view_cart():
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('login'))

    customer_id = session['user_id']
    conn = get_db_connection()
    cart_items = conn.execute('''SELECT Cart.CartID, MenuItem.Name, MenuItem.Description, MenuItem.Price, Cart.Quantity 
                                     FROM Cart 
                                     JOIN MenuItem ON Cart.ItemID = MenuItem.MenuItemID 
                                     WHERE Cart.CustomerID = ?''', (customer_id,)).fetchall()
    total_price = sum(item['Price'] * item['Quantity'] for item in cart_items)
    conn.close()
    return render_template('Cart.html', cart_items=cart_items, total_price=total_price)


@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('login'))

    customer_id = session['user_id']
    conn = get_db_connection()
    order_id = None

    try:
        # Start a transaction
        conn.execute('BEGIN')

        # Get the RestaurantID from the first cart item
        cart_item = conn.execute('''
            SELECT ItemID, RestaurantID FROM Cart
            JOIN MenuItem ON Cart.ItemID = MenuItem.MenuItemID
            WHERE Cart.CustomerID = ? LIMIT 1
        ''', (customer_id,)).fetchone()

        # If cart is not empty, proceed with checkout
        if cart_item:
            restaurant_id = cart_item['RestaurantID']

            # Insert new order and get order_id
            conn.execute('''
                INSERT INTO OrderTable (ReviewedBy, ReceivedBy, Status, SubmissionTime)
                VALUES (?, ?, 'Pending', CURRENT_TIMESTAMP)
            ''', (customer_id, restaurant_id))
            order_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

            # Get all cart items to be added to OrderDetails and Checkout
            cart_items = conn.execute('''
                SELECT CartID, ItemID, Quantity, (MenuItem.Price * Cart.Quantity) AS TotalPrice 
                FROM Cart JOIN MenuItem ON Cart.ItemID = MenuItem.MenuItemID 
                WHERE Cart.CustomerID = ?
            ''', (customer_id,)).fetchall()

            # Insert cart items into OrderDetails and Checkout tables
            for item in cart_items:
                conn.execute('''
                    INSERT INTO OrderDetails (OrderID, ItemID, Quantity, TotalPrice) 
                    VALUES (?, ?, ?, ?)
                ''', (order_id, item['ItemID'], item['Quantity'], item['TotalPrice']))
                conn.execute('''
                    INSERT INTO Checkout (CartID, OrderID) VALUES (?, ?)
                ''', (item['CartID'], order_id))

            # Clear the Cart table for the customer after checkout
            conn.execute('DELETE FROM Cart WHERE CustomerID = ?', (customer_id,))

            conn.commit()
            flash('Order placed successfully!', 'success')
        else:
            flash('Your cart is empty.', 'error')
            conn.rollback()

    except sqlite3.OperationalError as e:
        conn.rollback()
        flash('An error occurred while placing the order. Please try again.', 'error')
        print(e)
    finally:
        conn.close()

    if order_id:
        return redirect(url_for('track_order', order_id=order_id))
    else:
        return redirect(url_for('view_cart'))


@app.route('/track_order/<int:order_id>')
def track_order(order_id):
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('login'))

    conn = get_db_connection()
    order_row = conn.execute('SELECT * FROM OrderTable WHERE OrderID = ?', (order_id,)).fetchone()
    conn.close()

    if order_row is None:
        flash('Order not found.', 'error')
        return redirect(url_for('home'))

    # Convert the sqlite3.Row to a dictionary
    order = dict(order_row)

    # Convert the SubmissionTime from string to datetime object
    if order['SubmissionTime']:
        order['SubmissionTime'] = datetime.strptime(order['SubmissionTime'], '%Y-%m-%d %H:%M:%S')

    status_width = "0%"
    if order['Status'] == 'Pending':
        status_width = "25%"
    elif order['Status'] == 'Processing':
        status_width = "50%"
    elif order['Status'] == 'Delivered':
        status_width = "100%"
    elif order['Status'] == 'Cancelled':
        status_width = "100%"

    return render_template('TrackingOrder.html', order=order, status_width=status_width)


@app.route('/order_history')
def order_history():
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('login'))

    customer_id = session['user_id']
    conn = get_db_connection()
    try:
        query = '''
        SELECT ot.OrderID, ot.Status, ot.SubmissionTime, r.FirstName || ' ' || r.LastName AS RestaurantName
        FROM OrderTable ot
        JOIN Restaurant r ON ot.ReceivedBy = r.RestaurantID
        WHERE ot.ReviewedBy = ?
        '''
        orders = conn.execute(query, (customer_id,)).fetchall()
        conn.close()
        if not orders:
            flash('No orders found.')
        return render_template('OrderHistory.html', orders=orders)
    except sqlite3.OperationalError as e:
        flash('An error occurred while retrieving the order history. Please try again.')
        print(e)  # For debugging purposes
        return redirect(url_for('home'))


def get_restaurant_info(user_id):
    conn = get_db_connection()
    if session.get('user_type') == 'Restaurant':
        restaurant_info = conn.execute('SELECT * FROM Restaurant WHERE Username = ?', (user_id,)).fetchone()
    else:
        restaurant_info = None
    conn.close()
    return restaurant_info


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('You need to login first.', 'info')
        return redirect(url_for('login'))

    if session.get('user_type') == 'Restaurant':
        conn = get_db_connection()
        restaurant_info = conn.execute('SELECT * FROM Restaurant WHERE Username = ?', (session['username'],)).fetchone()
        conn.close()
        if restaurant_info:
            # Provide the restaurant info to the dashboard template
            return render_template('dashboard.html', restaurant=restaurant_info)
        else:
            flash('Restaurant not found.', 'error')
            return redirect(url_for('home'))
    else:
        # Handle non-restaurant users or redirect to a generic dashboard or home
        flash('Access denied. This area is for restaurant managers only.', 'error')
        return redirect(url_for('home'))


@app.route('/manage_restaurant', methods=['GET', 'POST'])
def manage_restaurant():
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        flash('You must be logged in as a restaurant to access this page.', 'error')
        return redirect(url_for('login'))

    restaurant_id = session.get('restaurant_id')

    # No need to handle POST request for updating hours here, so this part is removed

    # Database connection to retrieve current restaurant information and postal codes
    conn = get_db_connection()
    try:
        restaurant_info = conn.execute('SELECT * FROM Restaurant WHERE RestaurantID = ?', (restaurant_id,)).fetchone()
        postal_codes = conn.execute('SELECT Code FROM Codes WHERE RestaurantID = ?', (restaurant_id,)).fetchall()
    except sqlite3.Error as e:
        flash('An error occurred while retrieving restaurant information.', 'error')
        print(e)
    finally:
        conn.close()

    return render_template('ManageRestaurant.html', 
                           restaurant_info=restaurant_info, 
                           postal_codes=postal_codes)

@app.route('/update_hours/<int:restaurant_id>', methods=['POST'])
def update_hours(restaurant_id):
    # Check if the user is logged in and is the correct restaurant
    if 'user_id' not in session or session.get('restaurant_id') != restaurant_id:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))

    # Assuming opening_time and closing_time are passed in a 24-hour format, e.g., "09:00", "18:00"
    opening_time = request.form['opening_time']
    closing_time = request.form['closing_time']

    conn = get_db_connection()
    try:
        conn.execute('UPDATE Restaurant SET OpeningTime = ?, ClosingTime = ? WHERE RestaurantID = ?',
                     (opening_time, closing_time, restaurant_id))
        conn.commit()
        flash('Hours updated successfully!', 'success')
    except sqlite3.Error as e:
        conn.rollback()
        flash('Failed to update hours.', 'error')
        print(e)
    finally:
        conn.close()

    return redirect(url_for('manage_restaurant'))


@app.route('/add_code/<int:restaurant_id>', methods=['POST'])
def add_code(restaurant_id):
    if 'user_id' not in session or session.get('restaurant_id') != restaurant_id:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    
    new_code = request.form['code']
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO Codes (RestaurantID, Code) VALUES (?, ?)', (restaurant_id, new_code))
        conn.commit()
        flash('Postal code added successfully!', 'success')
    except sqlite3.Error as e:
        conn.rollback()
        flash('Failed to add postal code.', 'error')
        print(e)
    finally:
        conn.close()

    return redirect(url_for('manage_restaurant'))

@app.route('/delete_code/<int:restaurant_id>/<int:code>', methods=['POST'])
def delete_code(restaurant_id, code):
    if 'user_id' not in session or session.get('restaurant_id') != restaurant_id:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM Codes WHERE RestaurantID = ? AND Code = ?', (restaurant_id, code))
        conn.commit()
        flash('Postal code removed successfully!', 'success')
    except sqlite3.Error as e:
        conn.rollback()
        flash('Failed to remove postal code.', 'error')
        print(e)
    finally:
        conn.close()

    return redirect(url_for('manage_restaurant'))


@app.route('/manage_menu')
def manage_menu():
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('login'))
    
    # Assuming the session['user_id'] stores the restaurant's username
    restaurant_username = session['user_id']
    conn = get_db_connection()
    menu_items = conn.execute('SELECT * FROM MenuItem WHERE RestaurantID = (SELECT RestaurantID FROM Restaurant WHERE RestaurantID = ?)', (restaurant_username,)).fetchall()
    conn.close()

    return render_template('ManageMenu.html', menu_items=menu_items)



@app.route('/edit_menu_item/<int:item_id>', methods=['GET', 'POST'])
def edit_menu_item(item_id):
    if 'user_id' not in session:
        flash('Please login to access this page.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    if request.method == 'POST':
        # Use .get() to avoid KeyError and provide a default empty string
        name = request.form.get('name', '')
        price = request.form.get('price', '')
        description = request.form.get('description', '')

        if not (name and price and description):
            flash('Please provide all required fields.', 'error')
            return redirect(url_for('edit_menu_item', item_id=item_id))

        # Additional validation and sanitization as needed

        conn.execute('UPDATE MenuItem SET Name = ?, Price = ?, Description = ? WHERE MenuItemID = ?',
                     (name, price, description, item_id))
        conn.commit()
        conn.close()
        flash('Menu item updated successfully!', 'success')
        return redirect(url_for('manage_menu'))  # Ensure 'manage_menu' is the correct redirect endpoint
    else:
        item = conn.execute('SELECT * FROM MenuItem WHERE MenuItemID = ?', (item_id,)).fetchone()
        if item is None:
            flash('Menu item not found.', 'error')
            return redirect(url_for('manage_menu'))  # Ensure 'manage_menu' is the correct redirect endpoint
        return render_template('EditMenuItem.html', item=item)



@app.route('/delete_menu_item/<int:item_id>', methods=['POST'])
def delete_menu_item(item_id):
    # Check if the user is logged in and is a restaurant
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        flash('You need to be logged in as a restaurant to perform this action.', 'error')
        return redirect(url_for('login'))

    restaurant_username = session['user_id']  # Assuming the user_id in the session is the restaurant username

    # Connect to the database
    conn = get_db_connection()
    try:
        # Get the restaurant ID from the database using the username
        restaurant = conn.execute('SELECT RestaurantID FROM Restaurant WHERE RestaurantID = ?', (restaurant_username,)).fetchone()
        if restaurant:
            restaurant_id = restaurant['RestaurantID']

            # Delete the menu item if it belongs to the restaurant
            conn.execute('DELETE FROM MenuItem WHERE MenuItemID = ? AND RestaurantID = ?', (item_id, restaurant_id))
            conn.commit()
            flash('Menu item deleted successfully.', 'success')
        else:
            flash('Restaurant not found.', 'error')
    except sqlite3.Error as e:
        conn.rollback()
        flash('An error occurred. Please try again.', 'error')
        print(e)  # For debugging purposes
    finally:
        conn.close()

    return redirect(url_for('manage_menu'))


@app.route('/add_menu_item', methods=['GET', 'POST'])
def add_menu_item():
    # Check if the user is logged in and is a restaurant
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        flash('You need to be logged in as a restaurant to perform this action.', 'error')
        return redirect(url_for('login'))

    restaurant_username = session['user_id']  # Assuming the user_id in the session is the restaurant username

    if request.method == 'POST':
        # Get data from the form
        name = request.form['name']
        description = request.form['description']
        category=request.form['category']
        price = request.form['price']
        # Add more fields as necessary, e.g., category, picture

        # Connect to the database
        conn = get_db_connection()
        try:
            # Get the restaurant ID from the database using the username
            restaurant = conn.execute('SELECT RestaurantID FROM Restaurant WHERE RestaurantID = ?', (restaurant_username,)).fetchone()
            if restaurant:
                restaurant_id = restaurant['RestaurantID']

                # Insert the new item into the database
                conn.execute('INSERT INTO MenuItem (RestaurantID, Name, Description, Category, Price) VALUES (?, ?, ?, ?, ?)',
                             (restaurant_id, name, description, category, price))
                conn.commit()
                flash('New menu item added successfully.', 'success')
            else:
                flash('Restaurant not found.', 'error')
        except sqlite3.Error as e:
            conn.rollback()
            flash('An error occurred. Please try again.', 'error')
            print(e)  # For debugging purposes
        finally:
            conn.close()

        return redirect(url_for('manage_menu'))

    # If request.method == 'GET', show the add item form
    return render_template('AddMenuItem.html')



@app.route('/view_orders')
def view_orders():
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        flash('Access denied. Please log in as a restaurant.', 'error')
        return redirect(url_for('login'))

    restaurant_id = session.get('restaurant_id')  # Use the .get() method to avoid KeyError
    if not restaurant_id:
        flash('Restaurant ID not found in session. Please log in again.', 'error')
        return redirect(url_for('login'))

    pending_orders = get_pending_orders(restaurant_id)

    ongoing_orders = get_ongoing_orders(restaurant_id)

    completed_orders = get_completed_orders(restaurant_id)

    return render_template(
        'ViewOrders.html',
        pending_orders=pending_orders,
        ongoing_orders=ongoing_orders,
        completed_orders=completed_orders
    )

def get_pending_orders(restaurant_id):
    conn = get_db_connection()
    orders = conn.execute('''
        SELECT * FROM OrderTable WHERE Status = "Pending" AND ReceivedBy = ?
    ''', (restaurant_id,)).fetchall()
    conn.close()
    return orders


def get_ongoing_orders(restaurant_id):
    conn = get_db_connection()
    orders = conn.execute('''
            SELECT * FROM OrderTable WHERE Status = "Processing" AND ReceivedBy = ?
        ''', (restaurant_id,)).fetchall()
    conn.close()
    return orders


def get_completed_orders(restaurant_id):
    conn = get_db_connection()
    orders = conn.execute('''
            SELECT * FROM OrderTable WHERE Status = "Delivered" AND ReceivedBy = ?
        ''', (restaurant_id,)).fetchall()
    conn.close()
    return orders


@app.route('/accept_order/<int:order_id>', methods=['POST'])
def accept_order(order_id):
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE OrderTable SET Status = 'Processing' WHERE OrderID = ? AND Status = 'Pending'
        ''', (order_id,))
        conn.commit()
        flash('Order has been accepted and is now processing.', 'success')
    except Exception as e:
        conn.rollback()
        flash('An error occurred while updating the order status.', 'error')
        print(e)
    finally:
        conn.close()

    return redirect(url_for('view_orders'))


@app.route('/mark_as_delivered/<int:order_id>', methods=['POST'])
def mark_as_delivered(order_id):
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE OrderTable SET Status = 'Delivered' WHERE OrderID = ? AND Status = 'Processing'
        ''', (order_id,))
        conn.commit()
        flash('Order has been marked as delivered.', 'success')
    except Exception as e:
        conn.rollback()
        flash('An error occurred while updating the order status.', 'error')
        print(e)
    finally:
        conn.close()

    return redirect(url_for('view_orders'))


@app.route('/reject_order/<int:order_id>', methods=['POST'])
def reject_order(order_id):
    if 'user_id' not in session or session['user_type'] != 'Restaurant':
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE OrderTable SET Status = 'Cancelled' WHERE OrderID = ?
        ''', (order_id,))
        conn.commit()
        flash('Order has been cancelled.', 'success')
    except Exception as e:
        conn.rollback()
        flash('An error occurred while cancelling the order.', 'error')
        print(e)
    finally:
        conn.close()

    return redirect(url_for('view_orders'))


@app.route('/order_details/<int:order_id>')
def order_details(order_id):
    if 'user_id' not in session:
        flash('You need to login first', 'info')
        return redirect(url_for('login'))

    conn = get_db_connection()

    order_info = conn.execute('''
        SELECT ot.OrderID, ot.SubmissionTime, c.FirstName || ' ' || c.LastName AS CustomerName, 
               c.Address, c.City, c.PLZ
        FROM OrderTable ot
        LEFT JOIN Customer c ON ot.ReviewedBy = c.CustomerID
        WHERE ot.OrderID = ?
    ''', (order_id,)).fetchone()

    if not order_info:
        flash('Order not found.', 'error')
        return redirect(url_for('home'))

    items_ordered = conn.execute('''
    SELECT mi.Name, mi.Description, mi.Price, od.Quantity
    FROM OrderDetails od
    INNER JOIN MenuItem mi ON od.ItemID = mi.MenuItemID
    WHERE od.OrderID = ?
''', (order_id,)).fetchall()
    
    print(items_ordered)

    total_price = sum(item['Price'] * item['Quantity'] for item in items_ordered)

    conn.close()

    return render_template('OrderDetails.html', order_info=order_info, items_ordered=items_ordered,
                           total_price=total_price)
    
    

if __name__ == '__main__':
    app.run(debug=True)
