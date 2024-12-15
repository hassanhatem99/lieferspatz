-- Step 1: Create a new table with the desired schema
CREATE TABLE Orders_new (
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

-- Step 2: Copy data from the original table to the new table
INSERT INTO Orders_new (
    id, customer_id, business_id, item_id, quantity, additional_text, order_status, created_at
)
SELECT
    id, customer_id, business_id, item_id, quantity, additional_text, order_status, created_at
FROM Orders;

-- Step 3: Drop the old table
DROP TABLE Orders;

-- Step 4: Rename the new table to the original name
ALTER TABLE Orders_new RENAME TO Orders;



-- sqlite3 lieferpatz_database.sqlite     access the database
-- .read sql_commands.sql    run the commands in this file