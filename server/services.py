import jwt
import os
import ast
import boto3
import base64
from io import BytesIO
from dotenv import load_dotenv
from tempfile import NamedTemporaryFile
from fastapi import HTTPException, status, Depends, UploadFile
from fastapi.security import OAuth2PasswordBearer
from database import connection
from models import *
from datetime import datetime, timedelta, date
from typing import Optional
from fastapi.responses import JSONResponse

log = Log()

# ------------------ token ------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
s3 = boto3.resource("s3")
bucket = s3.Bucket(S3_BUCKET_NAME)


def create_access_token(username: str):
    expiration_time = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data = {"sub": username, "exp": expiration_time}
    encoded_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_token


# ------------------ user ------------------------
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        if username not in connection.root.users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        user_data = connection.root.users[username]
        log.log_info(f"{username}: get_current_user operation successful")
        return user_data
    except jwt.ExpiredSignatureError:
        log.log_error("Error in get_current_user: Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.DecodeError:
        log.log_error("Error in get_current_user: Could not decode token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not decode token"
        )
    except Exception as e:
        log.log_error(f"Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def get_user(username: str):
    try:
        user = connection.root.users.get(username)
        if user:
            log.log_info(f"{username}: get_user operation successful")
            return {"username": user.username, "password": user.password}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' not found",
            )
    except HTTPException as he:
        log.log_error(f"HTTPException in get_user: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in get_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


async def get_users():
    try:
        users = []
        for username, user in connection.root.users.items():
            users.append({"username": username, "password": user.password})
        log.log_info(f"get_users operation successful")
        return {"users": users}
    except Exception as e:
        log.log_error(f"Error in get_users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def create_user(username: str, password: str):
    try:
        if username in connection.root.users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User already exists"
            )
        user = User(username, password)
        connection.root.users[username] = user
        connection.transaction_manager.commit()
        log.log_info(f"User '{username}' created successfully")
        return {"username": username, "message": "User created successfully"}
    except HTTPException as he:
        log.log_error(f"HTTPException in create_user: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in create_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


async def delete_user(username: str):
    try:
        if username in connection.root.users:
            del connection.root.users[username]
            connection.transaction_manager.commit()
            log.log_info(f"User '{username}' deleted successfully")
            return {"message": f"User '{username}' deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' not found",
            )
    except HTTPException as he:
        log.log_error(f"HTTPException in delete_user: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in delete_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


async def login_user(username: str, password: str):
    if username in connection.root.users:
        user = connection.root.users[username]
        if user.password == password:
            access_token = create_access_token(username)  # Generate JWT token
            log.log_info(f"User '{username}' logged in successfully")
            return {"access_token": access_token, "token_type": "bearer"}
    log.log_error(f"HTTPException in login_user: Invalid username or password")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
    )


# ------------------ admin ------------------------
async def get_current_admin(token: str = Depends(oauth2_scheme)) -> Admin:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        if username not in connection.root.admins:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found"
            )
        admin_data = connection.root.admins[username]
        log.log_info(f"{username}: get_current_admin operation successful")
        return admin_data
    except jwt.ExpiredSignatureError:
        log.log_error("Error in get_current_admin: Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.DecodeError:
        log.log_error("Error in get_current_admin: Could not decode token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not decode token"
        )
    except Exception as e:
        log.log_error(f"Error in get_current_admin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def get_admin(username: str):
    try:
        admin = connection.root.admins.get(username)
        if admin:
            log.log_info(f"{username}: get_admin operation successful")
            return {"username": admin.username, "password": admin.password}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Admin '{username}' not found",
            )
    except HTTPException as he:
        log.log_error(f"HTTPException in get_admin: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in get_admin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


async def get_admins():
    try:
        admins = []
        for username, user in connection.root.admins.items():
            admins.append({"username": username, "password": user.password})
        log.log_info(f"get_admins operation successful")
        return {"admins": admins}
    except Exception as e:
        log.log_error(f"Error in get_admins: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def create_admin(username: str, password: str):
    try:
        if username in connection.root.admins:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Admin already exists"
            )
        admin = Admin(username, password)
        connection.root.admins[username] = admin
        connection.transaction_manager.commit()
        log.log_info(f"Admin '{username}' created successfully")
        return {"username": username, "message": "Admin created successfully"}
    except HTTPException as he:
        log.log_error(f"HTTPException in create_admin: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in create_admin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create admin",
        )


async def delete_admin(username: str):
    try:
        if username in connection.root.admins:
            del connection.root.admins[username]
            connection.transaction_manager.commit()
            log.log_info(f"Admin '{username}' deleted successfully")
            return {"message": f"Admin '{username}' deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Admin '{username}' not found",
            )
    except HTTPException as he:
        log.log_error(f"HTTPException in delete_admin: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in delete_admin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


async def login_admin(username: str, password: str):
    if username in connection.root.admins:
        user = connection.root.admins[username]
        if user.password == password:
            access_token = create_access_token(username)  # Generate JWT token
            log.log_info(f"Admin '{username}' logged in successfully")
            return {"access_token": access_token, "token_type": "bearer"}
    log.log_error(f"HTTPException in login_admin: Invalid username or password")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
    )


# ------------------ admin menu ------------------------
async def get_menu(menu_item: str):
    try:
        item = connection.root.menus.get(menu_item)
        if item:
            log.log_info(f"{menu_item}: get_menu operation successful")
            return {
                "name": item.name,
                "price": item.price,
                "description": item.description,
                "type": item.type,
                "cost": item.cost,
                "ingredients": item.ingredients,
                "photo": item.photo,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu '{menu_item}' not found",
            )
    except HTTPException as he:
        log.log_error(f"HTTPException in get_menu: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in get_menu: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


async def get_menus():
    try:
        menus = []
        for name, menu in connection.root.menus.items():
            menus.append(
                {
                    "name": menu.name,
                    "price": menu.price,
                    "description": menu.description,
                    "type": menu.type,
                    "cost": menu.cost,
                    "ingredients": menu.ingredients,
                    "photo": menu.photo,
                }
            )
        log.log_info(f"get_menus operation successful")
        return {"menus": menus}
    except Exception as e:
        log.log_error(f"Error in get_menus: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def add_menu(
    category: str,
    name: str,
    price: int,
    description: str,
    type: str,
    cost: int,
    ingredients: list,
    sweetness: int,
    photo: UploadFile,
):
    try:
        if name in connection.root.menus:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Menu already exists"
            )

        photo_url = None
        if photo:
            # Read the uploaded file content
            photo_content = photo.file.read()
            # Create a BytesIO object to wrap the content
            photo_content_bytesio = BytesIO(photo_content)
            # Decode the photo content from base64
            decoded_photo = base64.b64decode(photo_content_bytesio.read())
            # Upload the decoded photo content to the bucket
            bucket.upload_fileobj(BytesIO(decoded_photo), photo.filename)
            photo_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{photo.filename}"

        if category.upper() == "DRINK":
            menu = Drink(
                name, price, description, type, cost, ingredients, photo_url, sweetness
            )
        elif category.upper() == "DESSERT":
            menu = Dessert(name, price, description, type, cost, ingredients, photo_url)
        else:
            menu = MainDish(
                name, price, description, type, cost, ingredients, photo_url
            )

        connection.root.menus[name] = menu
        connection.transaction_manager.commit()
        log.log_info(f"{name}: add_menu operation successful")
        return {"message": "Menus registered successfully"}
    except HTTPException as he:
        log.log_error(f"HTTPException in add_menu: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in add_menu: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create menu",
        )


async def delete_menu(food_name: str):
    try:
        if food_name in connection.root.menus:
            del connection.root.menus[food_name]
            connection.transaction_manager.commit()
            log.log_info(f"{food_name}: delete_menu operation successful")
            return {"message": f"Menu Item '{food_name}' deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu Item '{food_name}' not found",
            )
    except HTTPException as he:
        log.log_error(f"HTTPException in delete_menu: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in delete_menu: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


async def edit_menu(
    food_name: str,
    category: Optional[str] = None,
    name: Optional[str] = None,
    price: Optional[int] = None,
    description: Optional[str] = None,
    type: Optional[str] = None,
    cost: Optional[int] = None,
    ingredients: Optional[str] = None,
    sweetness: Optional[int] = None,
):
    try:
        if food_name not in connection.root.menus:
            raise HTTPException(status_code=404, detail=f"Menu '{food_name}' not found")

        menu = connection.root.menus[food_name]

        if category is not None:
            menu.category = category
        if name is not None:
            if name != food_name:
                connection.root.menus[name] = connection.root.menus.pop(food_name)
            menu.name = name
        if price is not None:
            menu.price = price
        if description is not None:
            menu.description = description
        if type is not None:
            menu.type = type
        if cost is not None:
            menu.cost = cost
        if ingredients is not None:
            ingredients_list = ast.literal_eval(ingredients)
            menu.ingredients = ingredients_list
        if sweetness is not None:
            menu.sweetness = sweetness

        connection.transaction_manager.commit()

        log.log_info(f"{food_name}: edit_menu operation successful")
        return {"message": f"Menu '{food_name}' updated successfully"}
    except HTTPException as he:
        log.log_error(f"HTTPException in edit_menu: {he.detail.strip()}")
        raise
    except Exception as e:
        log.log_error(f"Error in edit_menu: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update menu information",
        )


# ------------ Cart ------------------
async def get_cart(username: str):
    try:
        if username in connection.root.users:
            user = connection.root.users[username]
            cart = []
            for food_name, quantity in user.cart.items():
                cart.append(
                    {
                        "name": food_name,
                        "quantity": quantity,
                        "price": connection.root.menus[food_name].price,
                    }
                )
            log.log_info(f"{username}: get_cart operation successful")
            return {"cart": cart}
        else:
            log.log_error(f"get_cart: User not found")
            return {"message": "User not found."}
    except Exception as e:
        log.log_error(f"Error in get_cart: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user cart.",
        )


async def add_cart(username: str, food_name: str, quantity: int):
    try:
        if food_name not in connection.root.menus:
            log.log_error(f"Error in add_cart: The menu doesn't have this food")
            return {"message": "The menu doesn't have this food"}
        if username in connection.root.users:
            user = connection.root.users[username]
            if food_name not in user.cart:
                user.cart[food_name] = quantity
            else:
                user.cart[food_name] += quantity
            connection.transaction_manager.commit()
            log.log_info(
                f"{food_name} added to {username}: add_cart operation successful"
            )
            return {"message": "Cart added successfully"}
    except Exception as e:
        log.log_error(f"Error in add_cart: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add menu",
        )


async def delete_cart(username: str, food_name: str, quantity: int = 1):
    try:
        if username in connection.root.users:
            user = connection.root.users[username]
            if food_name in user.cart:
                current_quantity = user.cart.get(food_name, 0)
                if quantity >= current_quantity:
                    del user.cart[food_name]
                else:
                    user.cart[food_name] -= quantity
                connection.transaction_manager.commit()
                log.log_info(
                    f"{food_name} deleted from {username}: delete_cart operation successful"
                )
                return {"message": "Cart deleted successfully"}
            else:
                log.log_error(
                    f"Error in delete_cart: Food item not found in user's cart list"
                )
                return {"error": "Food item not found in user's cart list"}
        else:
            log.log_error(f"Error in delete_cart: User not found")
            return {"error": "User not found"}
    except Exception as e:
        log.log_error(f"Error in delete_cart: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete cart",
        )


# ------------ Customer Order ------------------
async def get_orders(username: str):
    try:
        if username in connection.root.users:
            user = connection.root.users[username]
            orders = []
            for food_name, quantity in user.orders.items():
                orders.append(
                    {
                        "name": food_name,
                        "quantity": quantity,
                        "price": connection.root.menus[food_name].price,
                    }
                )
            log.log_info(f"{username}: get_orders operation successful")
            return {"orders": orders}
        else:
            log.log_error(f"get_orders: User not found")
            return {"message": "User not found."}
    except Exception as e:
        log.log_error(f"Error in get_orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user orders.",
        )


async def add_order(username: str, food_name: str, quantity: int):
    try:
        if food_name not in connection.root.menus:
            log.log_error(f"Error in add_order: The menu doesn't have this food")
            return {"message": "The menu doesn't have this food"}
        if username in connection.root.users:
            user = connection.root.users[username]
            if food_name not in user.orders:
                user.orders[food_name] = quantity
            else:
                user.orders[food_name] += quantity
            connection.transaction_manager.commit()
            log.log_info(
                f"{food_name} added to {username}: add_order operation successful"
            )
            return {"message": "Order added successfully"}
    except Exception as e:
        log.log_error(f"Error in add_order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add menu",
        )


async def delete_order(username: str, food_name: str, quantity: int = 1):
    try:
        if username in connection.root.users:
            user = connection.root.users[username]
            if food_name in user.orders:
                current_quantity = user.orders.get(food_name, 0)
                if quantity >= current_quantity:
                    del user.orders[food_name]
                else:
                    user.orders[food_name] -= quantity
                connection.transaction_manager.commit()
                log.log_info(
                    f"{food_name} deleted from {username}: delete_order operation successful"
                )
                return {"message": "Order deleted successfully"}
            else:
                log.log_error(
                    f"Error in delete_order: Food item not found in user's order list"
                )
                return {"error": "Food item not found in user's order list"}
        else:
            log.log_error(f"Error in delete_order: User not found")
            return {"error": "User not found"}
    except Exception as e:
        log.log_error(f"Error in delete_order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete order",
        )
        
        
async def place_order(username: str):
    try:
        if username in connection.root.users:
            user = connection.root.users[username]
            user.orders = user.cart
            user.cart = {}
            connection.transaction_manager.commit()
            log.log_info(
                f"{username}: place_order operation successful"
            )
            return {"message": "Order placed successfully"}
    except Exception as e:
        log.log_error(f"Error in place_order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to place order",
        )
    

# --------------------Table-------------------------
async def get_tables():
    try:
        all_table = []
        for i, table in connection.root.tables.items():
            all_table.append(
                {
                    "table_num": table.table_num,
                    "customers": table.customers,
                    "available": table.available,
                }
            )
        log.log_info(f"get_tables operation successful")
        return {"tables": all_table}
    except Exception as e:
        log.log_error(f"Error in get_orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def add_table(table_num: str):
    try:
        if table_num in connection.root.tables:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Table already exists"
            )
        table = Table(table_num)
        connection.root.tables[table_num] = table
        connection.transaction_manager.commit()
        log.log_info(f"Table {table_num}: Table added successfully")
        return {"message": "Table is added successfully"}
    except HTTPException as he:
        log.log_error(f"HTTPException in add_table: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in add_table: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add table",
        )


async def add_table_customer(table_num: str, user: str):
    try:
        if user not in connection.root.users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        if table_num not in connection.root.tables:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Table not found"
            )

        for table in connection.root.tables.values():
            if any(user == customer.username for customer in table.customers):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User '{user}' is already booked at another table",
                )

        connection.root.tables[table_num].customers.append(connection.root.users[user])
        connection.transaction_manager.commit()

        log.log_info(f"Table {table_num}: User '{user}' added to table successfully")
        return {"message": f"User '{user}' added to table '{table_num}' successfully"}
    except HTTPException as he:
        log.log_error(f"HTTPException in add_table_customer: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in add_table_customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def show_table_customer(table_num: int):
    try:
        if table_num in connection.root.tables:
            customers = [
                customer.username
                for customer in connection.root.tables[table_num].customers
            ]
            log.log_info(f"Table {table_num}: Retrieved customers successfully")
            return customers
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Table not found"
            )
    except HTTPException as he:
        log.log_error(f"HTTPException in show_table_customer: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in show_table_customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def show_table_orders(table_num: int):
    try:
        if table_num in connection.root.tables:
            all_orders = []

            for customer in connection.root.tables[table_num].customers:
                customer_orders = []
                for order_name in customer.orders:
                    order = {
                        "name": order_name,
                        "quantity": customer.orders[order_name],
                        "price": connection.root.menus[order_name].price
                    }
                    customer_orders.append(order)
                all_orders.extend(customer_orders)

            log.log_info(f"Table {table_num}: Retrieved orders successfully")
            return all_orders
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Table not found"
            )
    except HTTPException as he:
        log.log_error(f"HTTPException in show_table_orders: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in show_table_orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def show_table_payment(table_num: int):
    try:
        if table_num in connection.root.tables:
            total_payment = 0

            for customer in connection.root.tables[table_num].customers:
                for order in customer.orders:
                    total_payment += (connection.root.menus[order].price * int(customer.orders[order]))

            log.log_info(
                f"Table {table_num}: Retrieved payment information successfully"
            )
            return {"total_payment": total_payment}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Table not found"
            )
    except HTTPException as he:
        log.log_error(f"HTTPException in show_table_payment: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in show_table_payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def table_checkout(table_num: int):
    try:
        current_date = str(date.today())
        if table_num in connection.root.tables:
            table = connection.root.tables[table_num]
            if current_date not in connection.root.stats:
                connection.root.stats[current_date] = Stat(current_date, 0, 0)

            for customer in table.customers:
                for order in customer.orders:
                    connection.root.stats[current_date].income += (connection.root.menus[order].price * customer.orders[order])
                    connection.root.stats[current_date].cost += (connection.root.menus[order].cost * customer.orders[order])

                    point = customer.orders[order]
                    if order not in connection.root.popular:
                        connection.root.popular[order] = Popular(order, point)
                    else:
                        connection.root.popular[order].point += point
                        
                customer.orders.clear()
            table.customers.clear()
            connection.transaction_manager.commit()
            log.log_info(f"Table {table_num}: Checked out successfully")
            return {"message": f"Table {table_num} checked out successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Table not found"
            )
    except HTTPException as he:
        log.log_error(f"HTTPException in table_checkout: {he.detail}")
        raise
    except Exception as e:
        log.log_error(f"Error in table_checkout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def get_stats():
    try:
        all_stats = []
        for date, stat in connection.root.stats.items():
            all_stats.append({
                "date": stat.date, 
                "cost": stat.cost, 
                "income": stat.income
            })
        log.log_info(f"get_stats operation successful")
        return {"stats": all_stats}
    except Exception as e:
        log.log_error(f"Error in get_users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    
async def get_popularities():
    try:
        all_populars = []
        for dish, popular in connection.root.popular.items():
            all_populars.append({
                "dish": popular.dish, 
                "point": popular.point, 
            })
        log.log_info(f"get_popularities operation successful")
        return {"populars": all_populars}
    except Exception as e:
        log.log_error(f"Error in get_popularities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )