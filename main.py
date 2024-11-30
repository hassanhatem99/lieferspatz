from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.utils import secure_filename
import uuid
import os
from datetime import datetime


app = Flask(__name__)
app.secret_key = '64644364569843546843645'
database_name = "lieferpatz_database.sqlite"
UPLOAD_FOLDER = 'static/uploads/'
MENU_CATEGORIES = ['All', 'Starters', 'Main Course', 'Desserts', 'Beverages', 'Vegetarian', 'Seafood']

# Function to connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect(database_name)
    conn.row_factory = sqlite3.Row
    return conn

# function to add menu categories to the database
def add_menu_categories():
    conn = get_db_connection()
    cursor = conn.cursor()

    # clear the menuCategories table
    cursor.execute('DELETE FROM MenuCategories')

    # Iterate through the list and insert each category into the table
    for category in MENU_CATEGORIES:
        cursor.execute('''
            INSERT INTO MenuCategories (category)
            VALUES (?);
        ''', (category,))
    
    conn.commit()
    conn.close()






# this is the initial route that will show the main page of the website before user is logged in
@app.route('/')
def home():
    return render_template('index.html')

#########################################################################
## 
## CUSTOMER ROUTES START HERE
## 
#########################################################################

# route to register a customer and store details to the sqlite database
@app.route('/customer-register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        street = request.form['street']
        zip_code = request.form['zip_code']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM CustomerAccount WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user :
            flash('Failed!! User with this email already exists', 'danger')
            return render_template('customer/register.html')


        cursor.execute('''
            INSERT INTO CustomerAccount (FirstName, LastName, Email, street, zip_code, password)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, street, zip_code, password))

        conn.commit()
        conn.close()

        flash('Account created successfully...', 'success')
        return redirect(url_for('customer_login'))

    return render_template('customer/register.html')

# route to login user, check if supplied email and password is correct, if so then login the user
@app.route('/customer-login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM customerAccount WHERE email = ?', (email,))
        user = cursor.fetchone()

        conn.close()

        if user :
            if user['password'] == password:
                flash('Login successful!', 'success')

                # logout any current logged in user
                if session.get('user_id'):
                    session.clear()

                session['user_id'] = user['id']
                session['user_type'] = 'customer'
                session['user_name'] = user['firstname'] + ' ' + user['lastname']
                session['user_email'] = user['email']
                return redirect(url_for('customer_view_businesses'))
            else:
                flash('Failed!! Please check your password.', 'danger')

        else:
            flash('Failed!! Please check your email.', 'danger')

    return render_template('customer/login.html')

# route to view item in business menu
@app.route('/customer-view-businesses', methods=['GET', 'POST'])
def customer_view_businesses():
    conn = get_db_connection()
    cursor = conn.cursor()

    # first get user details
    cursor.execute('SELECT * FROM customerAccount WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()

    # Get the current time
    current_time = datetime.now().time()

    # Format the time as 'hh:mm'
    formatted_time = current_time.strftime('%H:%M')


    # next get all business that are open and supply within users zip code
    cursor.execute('''SELECT * FROM BusinessAccount 
                    WHERE LOWER(delivery_radius) LIKE LOWER(?) 
                        AND ? BETWEEN opening_hours AND closing_hours
                    ''', ('%' + user['zip_code'] + '%', formatted_time))

    items = cursor.fetchall()

    # cursor.execute('select SUBSTR(time(\'now\'), 1, 5)')
    
    # print(dict(cursor.fetchone()))


    conn.close()

    return render_template('customer/view-businesses.html', items=items)


# route to view item in business menu
@app.route('/customer-view-menu/<int:business_id>', methods=['GET', 'POST'])
def customer_view_menu(business_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        item_id = request.form['item_id']
        quantity = request.form['quantity']

        cursor.execute('INSERT INTO Cart (customer_id, item_id, quantity) VALUES (?, ?, ?)',
                        (session['user_id'], item_id, quantity))
        
        cursor.execute('SELECT Name FROM Items WHERE id = ?', (item_id))
        item = cursor.fetchone()
        conn.commit()
        
        flash(f'{item['Name']} (x{quantity}) Added to cart successfully...', 'success')


    # get all businesses for this business
    if 'category' in request.args and not request.args.get('category') == 'All':
        category = request.args.get('category')
        cursor.execute('''
            SELECT * FROM Items 
                WHERE business_id = ?
                       AND category = ?
        ''', (business_id, category))
    else:
        cursor.execute('''
            SELECT * FROM Items WHERE business_id = ?
        ''', (business_id,))
    items = cursor.fetchall()

  
    cursor.execute('''
        SELECT * FROM BusinessAccount WHERE id = ?
    ''', (business_id,))
    business = cursor.fetchone()

    cursor.execute('SELECT * FROM MenuCategories')
    categories = cursor.fetchall()


    conn.close()


    return render_template('customer/view-menu.html', items=items, business=business, categories=categories)


# route to view item in business menu
@app.route('/customer-view-cart', methods=['GET', 'POST'])
def customer_view_cart():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        if 'delete_item' in request.form:
            item_id = request.form['item_id']

            cursor.execute('''
                DELETE FROM Cart WHERE id = ?
            ''', (item_id,))
            conn.commit()

            flash(f'Item removed from cart successfully...', 'success')
            return redirect(url_for('customer_view_cart'))

        elif 'save_additional_text' in request.form:
            additional_text = request.form['additional_text']
            item_id = request.form['item_id']

            cursor.execute('''
                UPDATE Cart SET additional_text = ? WHERE id = ?
            ''', (additional_text, item_id,))
            conn.commit()
            

            flash(f'Restorant additional text saved successfully', 'success')
            return redirect(url_for('customer_view_cart'))

        elif 'checkout' in request.form:
            #TODO if customer has enough balance
            # get all items in cart
            cursor.execute('''
                SELECT * FROM Cart JOIN Items ON Cart.item_id = Items.id WHERE Cart.customer_id = ?
            ''', (session['user_id'],))
            items = cursor.fetchall()

            for item in items:
                # save all items in cart to the orders table
                cursor.execute('''
                    INSERT INTO Orders (customer_id, business_id, item_id, quantity, additional_text, order_status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (item['customer_id'], item['business_id'], item['item_id'], item['quantity'], item['additional_text'], 'processing'))

            conn.commit()

            # we can now delete items in the cart for this user
            cursor.execute('''
                DELETE FROM Cart WHERE customer_id = ?
            ''', (session['user_id'],))
            conn.commit()

            

            flash(f'Order Placed Sucessfully', 'success')
            return redirect(url_for('customer_view_orders'))

    # get all items in cart
    cursor.execute('''
        SELECT * FROM Cart JOIN Items ON Cart.item_id = Items.id WHERE Cart.customer_id = ?
        
    ''', (session['user_id'],))
    items = cursor.fetchall()

    conn.close()

    total_price = 0.0
    # calculate total price
    for item in items:
        total_price += item['price'] *  item['quantity']

    return render_template('customer/view-cart.html', items=items, total_price=total_price)


# route to view item in business menu
@app.route('/customer-view-orders', methods=['GET', 'POST'])
def customer_view_orders():
    conn = get_db_connection()
    cursor = conn.cursor()

    # get all items in orders table
    cursor.execute('''
        SELECT 
            *, strftime('%d/%m/%Y %H:%M:%S', Orders.created_at) as formatted_date
            FROM Orders JOIN Items ON Orders.item_id = Items.id
            WHERE Orders.customer_id = ?
            ORDER BY 
        CASE 
            WHEN Orders.order_status IN ('processing', 'preparing') THEN 0 
            ELSE 1 
        END, 
        Orders.created_at DESC
        
        
    ''', (session['user_id'],))
    items = cursor.fetchall()

    conn.close()

    # for row in items:
    #     # Convert the row to a dictionary for better readability
    #     row_dict = dict(row)
    #     print(row_dict)
    return render_template('customer/view-orders.html', items=items)






#########################################################################
## 
## BUSINESS ROUTES START HERE
## 
#########################################################################




# route to register a business and store details to the sqlite database
@app.route('/business-register', methods=['GET', 'POST'])
def business_register():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        street = request.form['street']
        city = request.form['city']
        zip_code = request.form['zip_code']
        # opening_hours = request.form['opening_hours']
        # delivery_radius = request.form['delivery_radius']
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM BusinessAccount WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user :
            flash('Failed!! User with this email already exists', 'danger')
            return render_template('business/register.html')


        # if no picture is selected we will use a default picture
        picture = '/static/bg.png'

        # check if a picture was selected
        if 'picture' in request.files:
            # picture selected, so upload it
            file = request.files['picture']

            if file and not file.filename == '':
                filename = str(uuid.uuid4()) + '-' + secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

                # save the path to the uploaded picture
                picture = f'/{UPLOAD_FOLDER}{filename}'
           




        cursor.execute('''
            INSERT INTO BusinessAccount (name, description, street, city, zip_code, email, password, picture_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, street, city, zip_code, email, password, picture))

        conn.commit()
        conn.close()

        flash('Account created successfully...', 'success')
        return redirect(url_for('business_login'))

    return render_template('business/register.html')

# route to login user, check if supplied email and password is correct, if so then login the user
@app.route('/business-login', methods=['GET', 'POST'])
def business_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM BusinessAccount WHERE email = ?', (email,))
        user = cursor.fetchone()

        conn.close()

        if user :
            if user['password'] == password:
                flash('Login successful!', 'success')
                # logout any current logged in user
                if session.get('user_id'):
                    session.clear()

                session['user_id'] = user['id']
                session['user_type'] = 'business'
                session['user_name'] = user['name']
                session['user_email'] = user['email']
                return redirect(url_for('business_view_items'))
            else:
                flash('Failed!! Please check your password.', 'danger')

        else:
            flash('Failed!! Please check your email.', 'danger')

    return render_template('business/login.html')


# route to add item in business menu
@app.route('/business-add-item', methods=['GET', 'POST'])
def business_add_item():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']

        category = None

        if 'category' in request.form:
            category = request.form['category']
            # if category is -1 then no gategory was selected
            if category == '-1':
                category = None

        conn = get_db_connection()
        cursor = conn.cursor()

        # if no picture is selected we will use a default picture
        picture = '/static/logo.png'

        # check if a picture was selected
        if 'picture' in request.files:
            # picture selected, so upload it
            file = request.files['picture']

            if file and not file.filename == '':
                filename = str(uuid.uuid4()) + '-' + secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

                # save the path to the uploaded picture
                picture = f'/{UPLOAD_FOLDER}{filename}'
           

        
        cursor.execute('''
            INSERT INTO Items (business_id, name, description, category, price, picture_link)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], name, description, category, price, picture))

        conn.commit()
        conn.close()

        flash('Item Added Sucessfully', 'sucess')
        return redirect(url_for('business_view_items'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM MenuCategories')
    categories = cursor.fetchall()

    return render_template('business/add-item.html', categories=categories)


# route to edit item in business menu
@app.route('/business-edit-item/<int:item_id>', methods=['GET', 'POST'])
def business_edit_item(item_id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']

        conn = get_db_connection()
        cursor = conn.cursor()


        # check if a picture was selected
        if 'picture' in request.files:
            # picture selected, so upload it
            file = request.files['picture']

            if file and not file.filename == '':
                filename = str(uuid.uuid4()) + '-' + secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

                # save the path to the uploaded picture
                picture = f'/{UPLOAD_FOLDER}{filename}'

                cursor.execute('''
                    UPDATE Items
                    SET picture_link=?
                    WHERE id=? 
                ''', (picture, item_id))


        
        cursor.execute('''
            UPDATE Items
            SET name=?, description=?, price=?
            WHERE id=? 
        ''', (name, description, price, item_id))

        conn.commit()
        conn.close()

        flash('Item Edited Sucessfully', 'success')
        return redirect(url_for('business_view_items'))


    conn = get_db_connection()
    cursor = conn.cursor()

    
    cursor.execute('''
        SELECT * FROM Items WHERE id = ?
    ''', (item_id,))
    item = cursor.fetchone()

    conn.close()


    return render_template('business/edit-item.html', item=item)

# route to delete item in business menu
@app.route('/business-delete-item/<int:item_id>', methods=['GET', 'POST'])
def business_delete_item(item_id):
  
    conn = get_db_connection()
    cursor = conn.cursor()

    
    cursor.execute('''
        DELETE FROM Items WHERE id = ?
    ''', (item_id,))
    conn.commit()
    conn.close()


    flash('Item Deleted Sucessfully', 'success')


    return redirect(url_for('business_view_items'))

# route to view item in business menu
@app.route('/business-view-items', methods=['GET', 'POST'])
def business_view_items():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM items WHERE business_id = ?', (session['user_id'],))
    items = cursor.fetchall()


    conn.close()

    return render_template('business/view-items.html', items=items)

# route to view item in business menu
@app.route('/business-view-orders', methods=['GET', 'POST'])
def business_view_orders():
    conn = get_db_connection()
    cursor = conn.cursor()

    if 'accept' in request.args:
        print('setting accept...')
        order_id = request.args.get('accept')

        cursor.execute('''
            UPDATE Orders
            SET order_status="preparing"
            WHERE id=? 
        ''', (order_id, ))

        conn.commit()
    elif 'reject' in request.args:
        order_id = request.args.get('reject')

        cursor.execute('''
            UPDATE Orders
            SET order_status="cancelled"
            WHERE id=? 
        ''', (order_id, ))

        conn.commit()
    elif 'complete' in request.args:
        order_id = request.args.get('complete')

        cursor.execute('''
            UPDATE Orders
            SET order_status="completed"
            WHERE id=? 
        ''', (order_id, ))

        conn.commit()
    


    # get all items in orders table
    cursor.execute('''
        SELECT 
            Orders.*,  Items.*, 
            strftime('%d/%m/%Y %H:%M:%S', Orders.created_at) as formatted_date,
            CustomerAccount.FirstName || ' ' || CustomerAccount.LastName as customer_name

            FROM Orders 
                JOIN Items ON Orders.item_id = Items.id 
                JOIN CustomerAccount ON Orders.customer_id = CustomerAccount.id
            WHERE Orders.business_id = ?
            ORDER BY 
                CASE 
                    WHEN Orders.order_status IN ('processing', 'preparing') THEN 0 
                    ELSE 1 
                END, 
                Orders.created_at DESC
        
    ''', (session['user_id'],))
    items = cursor.fetchall()

    conn.close()

    
    return render_template('business/view-orders.html', items=items)

# route to settings in business menu
@app.route('/business-settings', methods=['GET', 'POST'])
def business_settings():
    if request.method == 'POST':
        opening_hours = request.form['opening_hours']
        closing_hours = request.form['closing_hours']
        delivery_radius = request.form['delivery_radius']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
                UPDATE BusinessAccount 
                    SET opening_hours = ?,
                       closing_hours = ?,
                       delivery_radius = ?
                        WHERE id = ?
            ''', (opening_hours, closing_hours, delivery_radius, session['user_id']))
        conn.commit()
        conn.close()

        flash('Details Saved Sucessfully', 'sucess')
        return redirect(url_for('business_settings'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM BusinessAccount WHERE id = ?
    ''', (session['user_id'],))
    item = cursor.fetchone()

    conn.close()


    return render_template('business/settings.html', item=item)



@app.route('/logout', methods=['GET'])
def logout():
    if session.get('user_id'):
        session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    # call this function to add menu categories table
    add_menu_categories()
    # then now run the flask app
    app.run(debug=True)
