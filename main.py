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
        city = request.form['city']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the email already exists in the Account table
        cursor.execute('SELECT * FROM Account WHERE Email = ?', (email,))
        account = cursor.fetchone()

        if account:
            flash('Failed! User with this email already exists.', 'danger')
            return render_template('customer/register.html')

        try:
            # Insert into the base table (Account)
            cursor.execute('''
                INSERT INTO Account (Email, Password, Street, ZIPCode, City)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, password, street, zip_code, city))

            # Get the ID of the newly inserted Account
            cursor.execute('SELECT id FROM Account WHERE Email = ?', (email,))

            new_account = cursor.fetchone()

            # Insert into the derived table (CustomerAccount)
            cursor.execute('''
                INSERT INTO CustomerAccount (account_id, FirstName, LastName)
                VALUES (?, ?, ?)
            ''', (new_account['id'], first_name, last_name))  # Default balance

            conn.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('customer_login'))
        except Exception as e:
            # Rollback in case of any error
            conn.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return render_template('customer/register.html')
        finally:
            conn.close()

    return render_template('customer/register.html')

# route to login user, check if supplied email and password is correct, if so then login the user
@app.route('/customer-login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM Account WHERE Email = ?', (email,))
        account = cursor.fetchone()

        cursor.execute('SELECT * FROM CustomerAccount WHERE account_id = ?', (account['id'],))
        customer = cursor.fetchone()
        conn.close()

        if customer :
            if account['password'] == password:
                flash('Login successful!', 'success')

                # logout any current logged in user
                if session.get('user_id'):
                    session.clear()

                session['account_id'] = account['id']
                session['customer_id'] = customer['id']
                session['user_type'] = 'customer'
                session['user_name'] = customer['FirstName'] + ' ' + customer['LastName']
                session['user_email'] = account['Email']
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

    # Get user details
    cursor.execute('SELECT * FROM Account WHERE id = ?', (session['account_id'],))
    account = cursor.fetchone()

    # Get the current time
    current_time = datetime.now().time()
    formatted_time = current_time.strftime('%H:%M')

    # Get all businesses that are open and deliver within the user's ZIP code
    # Join BusinessAccount with Account to fetch location details
    cursor.execute('''
        SELECT b.*, a.Street, a.City, a.ZIPCode
        FROM BusinessAccount b
        JOIN Account a ON b.account_id = a.id
        WHERE LOWER(b.delivery_radius) LIKE LOWER(?) 
            AND ? BETWEEN b.opening_hours AND b.closing_hours
    ''', ('%' + account['ZIPCode'] + '%', formatted_time))

    businesses = cursor.fetchall()
    conn.close()

    return render_template('customer/view-businesses.html', businesses=businesses)


# route to view item in business menu
@app.route('/customer-view-menu/<int:business_id>', methods=['GET', 'POST'])
def customer_view_menu(business_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        item_id = request.form['item_id']
        quantity = request.form['quantity']

        cursor.execute('INSERT INTO Cart (customer_id, item_id, quantity) VALUES (?, ?, ?)',
                        (session['customer_id'], item_id, quantity))
        
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
            cursor.execute('SELECT balance FROM CustomerAccount WHERE id = ?', (session['customer_id'],))
            balance = cursor.fetchone()['balance']
            total_price = 0
            # get all items in cart
            cursor.execute('''
                SELECT * FROM Cart JOIN Items ON Cart.item_id = Items.id WHERE Cart.customer_id = ?
            ''', (session['customer_id'],))
            cart_items = cursor.fetchall()

            # Get the total price
            for cart_item in cart_items:
                total_price += cart_item['price'] * cart_item['quantity']
            
            print('price is',total_price)

            if balance >= total_price:
                for cart_item in cart_items:
                    # save all items in cart to the orders table
                    cursor.execute('''
                        INSERT INTO Orders (customer_id, business_id, item_id, quantity, additional_text, order_status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (cart_item['customer_id'], cart_item['business_id'], cart_item['item_id'], cart_item['quantity'], cart_item['additional_text'], 'processing'))
                            # we can now delete items in the cart for this user
                cursor.execute('''
                    DELETE FROM Cart WHERE customer_id = ?
                ''', (session['customer_id'],))

                new_balance = balance - total_price
                cursor.execute('''UPDATE CustomerAccount 
                                  SET balance = ?
                                  WHERE id = ?''', (new_balance, session['customer_id']))

                conn.commit()
                flash(f'Order Placed Sucessfully', 'success')

                return redirect(url_for('customer_view_orders'))
            else:
                flash(f"You don't have enough balance", 'danger')
                return redirect(url_for('customer_view_cart'))

    # get all items in cart
    cursor.execute('''
        SELECT * FROM Cart JOIN Items ON Cart.item_id = Items.id WHERE Cart.customer_id = ?
        
    ''', (session['customer_id'],))
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
        
        
    ''', (session['customer_id'],))
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

        cursor.execute('SELECT * FROM Account WHERE Email = ?', (email,))
        account = cursor.fetchone()

        if account :
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
                INSERT INTO Account (Email, Password, Street, ZIPCode, City)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, password, street, zip_code, city))

        # Get the ID of the newly inserted Account
        cursor.execute('SELECT id FROM Account WHERE Email = ?', (email,))

        new_account = cursor.fetchone()
         
        cursor.execute('''
                INSERT INTO BusinessAccount (account_id, name, description, picture_link)
                VALUES (?, ?, ?, ?)
                ''', (new_account['id'], name, description, picture))

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

        cursor.execute('SELECT * FROM Account WHERE Email = ?', (email,))
        account = cursor.fetchone()

        cursor.execute('SELECT * FROM BusinessAccount WHERE account_id = ?', (account['id'],))
        business = cursor.fetchone()
        conn.close()

        if business :
            if account['password'] == password:
                flash('Login successful!', 'success')

                # logout any current logged in user
                if session.get('account_id'):
                    session.clear()

                session['account_id'] = account['id']
                session['business_id'] = business['id']
                session['user_type'] = 'business'
                session['user_name'] = business['name']
                session['user_email'] = account['Email']
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

        business = cursor.fetchone()

        
        cursor.execute('''
                INSERT INTO Items (business_id, Name, Description, category, Price, picture_link)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (session['business_id'], name, description, category, price, picture))

        conn.commit()
        conn.close()

        flash('Item Added Sucessfully', 'success')
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

    cursor.execute('SELECT * FROM items WHERE business_id = ?', (session['business_id'],))
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
        
    ''', (session['business_id'],))
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
                        WHERE account_id = ?
            ''', (opening_hours, closing_hours, delivery_radius, session['account_id']))
        conn.commit()
        conn.close()

        flash('Details Saved Sucessfully', 'success')
        return redirect(url_for('business_settings'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM BusinessAccount WHERE account_id = ?
    ''', (session['account_id'],))
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
