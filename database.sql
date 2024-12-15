
-------------------- Lieferpatz Database--------------------
-- CREATE DATABASE Lieferpatz;
-- Creating Account Table (Generalized Entity)

CREATE TABLE Account (
    id INTEGER PRIMARY KEY NOT NULL,
    Email VARCHAR(50) NOT NULL UNIQUE,
    Password VARCHAR(25) NOT NULL,
    Street VARCHAR(25),
    ZIPCode VARCHAR(10),
    City VARCHAR(255) NOT NULL
);

-- Creating CustomerAccount Table (Inherits Account)
CREATE TABLE CustomerAccount (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName VARCHAR(25) NOT NULL,
    LastName VARCHAR(25) NOT NULL,
    balance FLOAT DEFAULT 100,

    account_id INTEGER NOT NULL REFERENCES Account(id)
);

-- Creating BusinessAccount Table
CREATE TABLE BusinessAccount (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    opening_hours VARCHAR(100),
    closing_hours VARCHAR(100),
    delivery_radius TEXT,
    picture_link VARCHAR(255),
    
    account_id INTEGER NOT NULL REFERENCES Account(id)
);

-- Creating Menu Table
CREATE TABLE Menu (
    MenuID INT PRIMARY KEY,
    Appetizers TEXT,
    Drinks TEXT,
    Dessert TEXT,
    MainDishes TEXT
);

-- Creating Item Table
CREATE TABLE Items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Name VARCHAR(255),
    Description TEXT,
    category VARCHAR(255),
    Price DECIMAL(10, 2),
    picture_link VARCHAR(255),

    business_id INTEGER NOT NULL REFERENCES BusinessAccount(id)
    
);

-- Creating Cart Table
CREATE TABLE Cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    quantity INTEGER,
    additional_text TEXT,

    customer_id INTEGER NOT NULL REFERENCES CustomerAccount(id)
    
);
-- Creating Orders Table
CREATE TABLE Orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES CustomerAccount(id),
    business_id INTEGER NOT NULL REFERENCES BusinessAccount(id),
    item_id INTEGER,
    quantity INTEGER,
    additional_text TEXT,
    order_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT CHK_Status CHECK (order_status IN ('processing', 'preparing', 'cancelled', 'completed'))
);


-- Creating Orders Table
CREATE TABLE MenuCategories (
    category VARCHAR(255)
);





-- Creating OrderHistory Table
CREATE TABLE OrderHistory (
    CustomerEmail VARCHAR(50),
    BusinessEmail VARCHAR(50),
    FOREIGN KEY (CustomerEmail) REFERENCES CustomerAccount(Email),
    FOREIGN KEY (BusinessEmail) REFERENCES BusinessAccount(Email)
);

-- Relationship tables
CREATE TABLE B_Edit_Menu (
    B_Email VARCHAR(50) primary key,
    ID INT,
    FOREIGN KEY (B_Email) REFERENCES BusinessAccount(Email),
    FOREIGN KEY (ID) REFERENCES Menu(ID)
);

CREATE TABLE B_Has_Menu (
    B_Email VARCHAR(50) primary key,
    ID INT,
    FOREIGN KEY (B_Email) REFERENCES BusinessAccount(Email),
    FOREIGN KEY (ID) REFERENCES Menu(ID)
);


CREATE TABLE M_ConsistsOfItems(
    ID INT Primary Key,
    Name VARCHAR(25),
    FOREIGN KEY (ID) REFERENCES Menu(ID),
    FOREIGN KEY (Name) REFERENCES Item(Name)
);

CREATE TABLE C_MakesOrders (
    C_Email VARCHAR(50),
    OrderID INT Primary Key,
    FOREIGN KEY (C_Email) REFERENCES CustomerAccount(Email),
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID)
);

CREATE TABLE H_ContainsOrders (
    CustomerEmail VARCHAR(50),
    BusinessEmail VARCHAR(50),
    OrderID INT Primary Key ,
    FOREIGN KEY (CustomerEmail) REFERENCES CustomerAccount(Email),
    FOREIGN KEY (BusinessEmail) REFERENCES BusinessAccount(Email),
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID)
);

CREATE TABLE B_C_ViewsHistory (
    Email VARCHAR(50) Primary Key,
    CustomerEmail VARCHAR(50),
    BusinessEmail VARCHAR(50),
    FOREIGN KEY (Email) REFERENCES Account(Email),
    FOREIGN KEY (CustomerEmail) REFERENCES CustomerAccount(Email),
    FOREIGN KEY (BusinessEmail) REFERENCES BusinessAccount(Email)
);

	CREATE TABLE B_SeeOrders (
    b_Email VARCHAR(50),
    OrderID INT Primary Key ,
    FOREIGN KEY (b_Email) REFERENCES BusinessAccount(Email),
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID)
);

CREATE TABLE O_ConsistsOfItems (
    OrderID INT,
   IT_Name VARCHAR(25) Primary key,
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID),
    FOREIGN KEY (IT_Name) REFERENCES Item(Name)
);






-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------
-- ----------------------------------------------



-- create dummy test data


-- INSERT INTO BusinessAccount (name, description, street, city, zip_code, opening_hours, closing_hours, delivery_radius, email, password)
-- VALUES 
-- ("TEST restrant", "A very good resturant", "street", "city", "A001", "08:00", "23:10","A001 A002 A258", "admin@gmail.com", "12345678"),
-- ("foo", "Best food", "street", "city", "A001", "08:00", "00:00","A001 A002 A258", "admin1@gmail.com", "12345678");


-- INSERT INTO Items (business_id, name, description, price, picture_link)
-- VALUES ('1', "Burger", "best burger around", "7.50", "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/McDonald%27s_Quarter_Pounder_with_Cheese%2C_United_States.jpg/1135px-McDonald%27s_Quarter_Pounder_with_Cheese%2C_United_States.jpg"),
--  ('1', "Chips", "MEga chips", "17.50", "https://upload.wikimedia.org/wikipedia/commons/8/83/French_Fries.JPG");

-- INSERT INTO CustomerAccount (FirstName, LastName, Email, street, zip_code, password)
-- VALUES ('James', 'Doe', "foo@gmail.com", "street", "A001", "12345678");
