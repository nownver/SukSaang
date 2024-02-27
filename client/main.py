import time
import js
from pyscript import document
import requests
from abc import ABC, abstractmethod


def check_token():
    location_path = js.window.location.pathname
    if location_path in ["/", "/login", "/register", "/admin_login", "/admin_register"]:
        return

    access_token = js.window.localStorage.getItem("access_token")
    if not access_token:
        js.window.location.href = "/"
    else:
        if location_path.startswith("/admin"):
            url = "http://localhost:8000/admins/me"
        else:
            url = "http://localhost:8000/users/me"
            
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            js.window.location.href = "/"


def fetch_user_info():
    access_token = js.window.localStorage.getItem("access_token")
    if access_token:
        url = "http://localhost:8000/users/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            username = data.get("username")
            return username
        else:
            print("Error fetching user info:", response.text)
    else:
        print("Access token not found. User not logged in.")


class AbstractWidget(ABC):
    def __init__(self, element_id):
        self.element_id = element_id
        self._element = None
        check_token()

    @property
    def element(self):
        if not self._element:
            self._element = document.querySelector(f"#{self.element_id}")
        return self._element

    @abstractmethod
    def drawWidget(self):
        pass


class Layout(AbstractWidget):
    def __init__(self, element_id):
        AbstractWidget.__init__(self, element_id)

    def drawWidget(self, widgets):
        self.content = document.createElement("div")
        self.content.id = "content"
        self.content.className = "pt-24 min-h-screen h-full min-w-fit w-full "
        if js.window.location.pathname.startswith("/admin"):
            self.content.className += (
                "bg-gradient-to-br from-zinc-950 via-gray-800 to-gray-700"
            )
        else:
            self.content.className += (
                "bg-gradient-to-br from-zinc-950 via-gray-600 to-gray-500"
            )
        self.element.appendChild(self.content)

        for widget in widgets:
            widget.drawWidget()


class Welcome(AbstractWidget):
    def __init__(self, element_id):
        AbstractWidget.__init__(self, element_id)

    def redirect_to_user_login(self, event):
        js.window.location.href = "/login"

    def redirect_to_admin_login(self, event):
        js.window.location.href = "/admin_login"

    def drawWidget(self):
        content = document.createElement("div")
        content.innerHTML = f"""
            <div class="flex flex-row justify-center items-center gap-20 mt-36 pb-8">
                <div class="user flex flex-col justify-center items-center gap-6 cursor-pointer hover:scale-105 duration-500">
                    <img class="w-44 h-44" src="/user.svg"/>
                    <p class="text-white text-3xl font-bold">User</p>
                </div>
                <div class="admin flex flex-col justify-center items-center gap-6 cursor-pointer hover:scale-105 duration-500">
                    <img class="w-44 h-44" src="/admin.svg"/>
                    <p class="text-white text-3xl font-bold">Admin</p>
                </div>
            </div>
        """
        self.element.appendChild(content)

        user_element = content.querySelector(".user")
        user_element.onclick = self.redirect_to_user_login

        admin_element = content.querySelector(".admin")
        admin_element.onclick = self.redirect_to_admin_login


class Navbar(AbstractWidget):
    def __init__(self, element_id):
        AbstractWidget.__init__(self, element_id)

    def redirect_to_root(self, event):
        js.window.location.href = "/"

    def drawWidget(self):
        self.navbar = document.createElement("div")
        self.navbar.className = "backdrop-blur-lg w-screen h-24 text-white flex justify-center items-center fixed z-10"
        self.title = document.createElement("a")
        self.title.innerHTML = "SukSaang"
        self.title.className = "font-signature font-extrabold text-5xl cursor-pointer"
        self.title.onclick = self.redirect_to_root
        self.navbar.appendChild(self.title)
        self.element.appendChild(self.navbar)


class NotFound(AbstractWidget):
    def __init__(self, element_id):
        AbstractWidget.__init__(self, element_id)

    def drawWidget(self):
        self.text = document.createElement("h1")
        self.text.className = "text-3xl text-white"
        self.text.innerHTML = "404 NOT FOUND"
        self.element.appendChild(self.text)


class Register(AbstractWidget):
    def __init__(self, element_id):
        AbstractWidget.__init__(self, element_id)

    def redirect_to_login(self, event):
        if js.window.location.pathname == "/register":
            js.window.location.href = "/login"
        elif js.window.location.pathname == "/admin_register":
            js.window.location.href = "/admin_login"

    def register_click(self, event):
        username = self.username_input.value
        password = self.password_input.value

        if js.window.location.pathname == "/register":
            url = "http://localhost:8000/users"
        elif js.window.location.pathname == "/admin_register":
            url = "http://localhost:8000/admins"
        data = {"username": username, "password": password}
        headers = {
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            print("Register successful!")
            js.window.location.href = "/login"
        else:
            print("Error:", response.text)
            self.error_message.innerHTML = response.text

    def drawWidget(self):
        self.register = document.createElement("div")
        self.register.className = (
            "flex flex-col justify-center items-center w-screen gap-12 pt-10"
        )

        self.register_title = document.createElement("h3")
        self.register_title.innerHTML = "Sign Up"
        self.register_title.className = "text-4xl font-semibold font-medium text-white"
        self.register.appendChild(self.register_title)

        self.box = document.createElement("div")
        self.box.className = "flex flex-col gap-6"

        self.username_box = document.createElement("div")
        self.username_header = document.createElement("p")
        self.username_header.className = "text-base text-gray-300 font-light my-3"
        self.username_header.innerHTML = "Username"
        self.username_input = document.createElement("input")
        self.username_input.type = "text"
        self.username_input.className = (
            "w-96 h-10 rounded-lg border border-gray-300 px-3"
        )

        self.password_box = document.createElement("div")
        self.password_header = document.createElement("p")
        self.password_header.className = "text-base text-gray-300 font-light my-3"
        self.password_header.innerHTML = "Password"
        self.password_input = document.createElement("input")
        self.password_input.type = "password"
        self.password_input.className = (
            "w-96 h-10 rounded-lg border border-gray-300 px-3"
        )

        self.button_box = document.createElement("div")
        self.button_register = document.createElement("button")
        self.button_register.className = "w-96 h-16 bg-orange-500 shadow-md rounded-full text-white text-lg font-medium my-4"
        self.button_register.innerHTML = "Register"
        self.button_register.onclick = self.register_click

        self.question_box = document.createElement("div")
        self.question_box.className = "flex flex-row justify-center"
        self.question_text = document.createElement("a")
        self.question_text.className = "text-gray-400 cursor-pointer hover:underline"
        self.question_text.innerHTML = "Already have an account?"
        self.question_text.onclick = self.redirect_to_login

        self.username_box.appendChild(self.username_header)
        self.username_box.appendChild(self.username_input)
        self.password_box.appendChild(self.password_header)
        self.password_box.appendChild(self.password_input)
        self.button_box.appendChild(self.button_register)
        self.question_box.appendChild(self.question_text)

        self.error_message = document.createElement("p")
        self.error_message.className = "text-red-500"

        self.box.appendChild(self.username_box)
        self.box.appendChild(self.password_box)
        self.box.appendChild(self.button_box)
        self.box.appendChild(self.question_box)
        self.register.appendChild(self.box)
        self.register.appendChild(self.error_message)
        self.element.appendChild(self.register)


class Login(AbstractWidget):
    def __init__(self, element_id):
        AbstractWidget.__init__(self, element_id)

    def redirect_to_register(self, event):
        if js.window.location.pathname == "/login":
            js.window.location.href = "/register"
        elif js.window.location.pathname == "/admin_login":
            js.window.location.href = "/admin_register"

    def login_click(self, event):
        username = self.username_input.value
        password = self.password_input.value

        if js.window.location.pathname == "/login":
            url = "http://localhost:8000/users/login"
        elif js.window.location.pathname == "/admin_login":
            url = "http://localhost:8000/admins/login"
        data = {"username": username, "password": password}
        headers = {
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                access_token = data["access_token"]
                print("Login successful!")
                js.window.localStorage.setItem("access_token", access_token)
                js.window.location.href = "/home"
            else:
                message = data.get("detail", "Unknown error")
                print("Login failed:", message)
        else:
            print("Error:", response.text)
            self.error_message.innerHTML = response.text

    def drawWidget(self):
        self.login = document.createElement("div")
        self.login.className = (
            "flex flex-col justify-center items-center w-screen gap-12 pt-10"
        )

        self.login_title = document.createElement("h3")
        self.login_title.innerHTML = "Login"
        self.login_title.className = "text-4xl font-semibold font-medium text-white"
        self.login.appendChild(self.login_title)

        self.box = document.createElement("div")
        self.box.className = "flex flex-col gap-6"

        self.username_box = document.createElement("div")
        self.username_header = document.createElement("p")
        self.username_header.className = "text-base text-gray-300 font-light my-3"
        self.username_header.innerHTML = "Username"
        self.username_input = document.createElement("input")
        self.username_input.type = "text"
        self.username_input.className = (
            "w-96 h-10 rounded-lg border border-gray-300 px-3"
        )

        self.password_box = document.createElement("div")
        self.password_header = document.createElement("p")
        self.password_header.className = "text-base text-gray-300 font-light my-3"
        self.password_header.innerHTML = "Password"
        self.password_input = document.createElement("input")
        self.password_input.type = "password"
        self.password_input.className = (
            "w-96 h-10 rounded-lg border border-gray-300 px-3"
        )

        self.button_box = document.createElement("div")
        self.button_login = document.createElement("button")
        self.button_login.className = "w-96 h-16 bg-orange-500 shadow-md rounded-full text-white text-lg font-medium my-4"
        self.button_login.innerHTML = "Login"
        self.button_login.onclick = self.login_click

        self.question_box = document.createElement("div")
        self.question_box.className = "flex flex-row justify-center"
        self.question_text = document.createElement("a")
        self.question_text.className = "text-gray-400 cursor-pointer hover:underline"
        self.question_text.innerHTML = "Don't have an account?"
        self.question_text.onclick = self.redirect_to_register

        self.username_box.appendChild(self.username_header)
        self.username_box.appendChild(self.username_input)
        self.password_box.appendChild(self.password_header)
        self.password_box.appendChild(self.password_input)
        self.button_box.appendChild(self.button_login)
        self.question_box.appendChild(self.question_text)

        self.error_message = document.createElement("p")
        self.error_message.className = "text-red-500"

        self.box.appendChild(self.username_box)
        self.box.appendChild(self.password_box)
        self.box.appendChild(self.button_box)
        self.box.appendChild(self.question_box)
        self.login.appendChild(self.box)
        self.login.appendChild(self.error_message)
        self.element.appendChild(self.login)


class Home(AbstractWidget):
    def __init__(self, element_id):
        AbstractWidget.__init__(self, element_id)
        self.restaurant_name = None
        self.username = fetch_user_info()

    def redirect_to_menu(self, event):
        js.window.location.href = "/menu"

    def drawWidget(self):
        content = document.createElement("div")
        content.innerHTML = f"""
            <div class="h-full flex flex-col justify-center items-center gap-10 text-white pb-4">
                <div class="flex flex-row justify-around w-full">
                    <div class="cursor-pointer w-14">POINTS</div>
                    <div class="cursor-pointer w-14">MENU</div>
                </div>
                <img src="/restaurant.svg" class="w-48 h-48" />
                <div class="rounded-full bg-zinc-700 text-lg font-base px-20 py-4">
                    Welcome, {self.username}
                </div>
                <div class="flex flex-row gap-4">
                    <div class="order rounded-full bg-zinc-700 text-lg font-base px-20 py-14 w-[250px] flex justify-center items-center cursor-pointer">
                        Order
                    </div>
                    <div class="rounded-full bg-zinc-700 text-lg font-base px-20 py-14 w-[250px] flex justify-center items-center text-center cursor-pointer">
                        Leave Feedback
                    </div>
                </div>
            </div>
        """
        self.element.appendChild(content)

        order_box = content.querySelector(".order")
        order_box.onclick = self.redirect_to_menu


class Menu(AbstractWidget):
    def __init__(self, element_id):
        AbstractWidget.__init__(self, element_id)
        self.menu = None
        self.categories = ["rice", "noodle", "pasta", "steak", "soup", "sides"]
        self.fetch_menu_info()
        self.opened_modal = None

    def fetch_menu_info(self):
        url = "http://localhost:8000/menus"
        response = requests.get(url)
        if response.status_code == 200:
            self.menu = response.json()["menus"]
        else:
            print("Error fetching menu:", response.text)

    def handle_menu_item_click(self, event):
        if self.opened_modal:
            self.opened_modal.close_modal()
        menu_item_name = event.currentTarget.querySelector("h3").textContent
        document.body.style.overflow = "hidden"
        self.opened_modal = Detail("content", menu_item_name)
        self.opened_modal.drawWidget()

    def drawWidget(self):
        svg_images = ""
        for category in self.categories:
            svg_images += f"""
                <div class="flex flex-col justify-center items-center hover:scale-105 duration-300 cursor-pointer">
                    <img class="w-24 h-24 m-1" src="/category/{category}.svg" />
                    <p class="capitalize font-light text-base">{category}</p>
                </div>
            """

        menu_container = ""
        for item in self.menu:
            menu_container += f"""
                <div class="menu-item flex flex-col justify-center items-center hover:scale-105 duration-300 cursor-pointer">
                    <img class="w-36 w-36 mb-1" src="https://img.freepik.com/free-vector/illustration-gallery-icon_53876-27002.jpg" />
                    <h3 class="capitalize font-light text-sm sm:text-lg">{item['name']}</h3>
                    <p class="text-sm font-light">฿ {item['price']}</p>
                </div>
            """

        content = document.createElement("div")
        content.innerHTML = f"""
            <div class="flex flex-col justify-center items-center text-gray-700">
                <div class="w-full">
                    <div class="text-2xl font-extralight bg-zinc-300 p-6">
                        Categories
                    </div>
                    <div class="flex flex-row gap-8 bg-zinc-200 border-b border-slate-400 border-opacity-75 p-8">
                        {svg_images}
                    </div>
                </div>
                <div class="w-full">
                    <div class="text-2xl font-extralight bg-orange-200 p-6">
                        Recommended
                    </div>
                    <div class="flex flex-row gap-8 bg-zinc-200 border-b border-slate-400 border-opacity-75 p-10">
                        {menu_container}
                    </div>
                </div>
                <div class="w-full">
                    <div class="text-2xl font-extralight bg-orange-200 p-6">
                        Most Popular
                    </div>
                    <div class="flex flex-row gap-8 bg-zinc-200 border-b border-slate-400 border-opacity-75 p-10">
                        {menu_container}
                    </div>
                </div>
                <div class="fixed bottom-0 right-0 rounded-lg bg-zinc-400 z-10 py-4 px-6 flex justify-center items-center gap-4 cursor-pointer" onclick="window.location.href='/cart'">
                    <img class="w-10 h-10" src="/cart.svg"/>
                    <p class="hidden sm:block text-white">Total Amount: ฿ {0}</p>
                </div>
            </div>
        """
        self.element.appendChild(content)

        menu_items = self.element.querySelectorAll(".menu-item")
        for menu_item in menu_items:
            menu_item.onclick = self.handle_menu_item_click


class Detail(AbstractWidget):
    def __init__(self, element_id, menu_item):
        AbstractWidget.__init__(self, element_id)
        self.menu_item = menu_item
        self.item = None
        self.quantity = 1
        self.fetch_menu_item_info()
        self.modal_content = None

    def fetch_menu_item_info(self):
        url = f"http://localhost:8000/menus/{self.menu_item}"
        response = requests.get(url)
        if response.status_code == 200:
            self.item = response.json()
        else:
            print("Error fetching menu item:", response.text)

    def close_modal(self, event=None):
        if self.modal_content:
            self.element.removeChild(self.modal_content)
            document.body.style.overflow = "auto"
            self.modal_content = None

    def add_to_cart(self, event, quantity):
        username = fetch_user_info()
        food_name = self.item["name"]

        url = f"http://localhost:8000/users/{username}/orders?food_name={food_name}&quantity={quantity}"
        headers = {
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers)

        if response.status_code == 200:
            print("Succesfully Added to Cart")
            self.add_button.textContent = "Added to Cart"
            self.add_button.className = "text-green-500"
        else:
            print("Error:", response.text)
            self.add_button.textContent = "Failed to Add to Cart"
            self.add_button.className = "text-red-500"

    def drawWidget(self):
        self.modal_content = document.createElement("div")
        self.modal_content.innerHTML = f"""
            <div class="w-1/2 bg-zinc-500 rounded-lg p-8 border border-gray-300 shadow-lg fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                <span class="close text-white cursor-pointer">&times;</span>
                <div class="flex flex-col justify-center items-center text-white gap-6">
                    <img class="w-44 w-44" src="https://img.freepik.com/free-vector/illustration-gallery-icon_53876-27002.jpg" />
                    <p class="font-semibold text-lg">{self.item['name']}</p>
                    <ul class="list-disc font-extralight text-sm">
                        <li>
                            <span class="font-semibold mr-1">Price: </span> ฿{self.item['price']}
                        </li>
                        <li>
                            <span class="font-semibold mr-1">Description: </span> {self.item['description']}
                        </li>
                        <li>
                            <span class="font-semibold mr-1">Type: </span> {self.item['type']}
                        </li>
                        <li>
                            <span class="font-semibold mr-1">Ingredients: </span> {self.item['ingredients']['data']}
                        </li>
                    </ul>
                    <div class="flex flex-row gap-4">
                        <button class="decrement"> - </button>
                        <p class="quantity">{self.quantity}</p>
                        <button class="increment"> + </button>
                    </div>
                    <button class="add-btn hover:text-blue-400">Add to Cart</button>
                </div>
            </div>
        """
        self.element.appendChild(self.modal_content)

        close_button = self.modal_content.querySelector(".close")
        close_button.onclick = self.close_modal

        self.quantity_element = self.modal_content.querySelector(".quantity")

        def decrement(event):
            if self.quantity > 1:
                self.quantity -= 1
                self.quantity_element.textContent = self.quantity

        def increment(event):
            self.quantity += 1
            self.quantity_element.textContent = self.quantity

        decrement_button = self.modal_content.querySelector(".decrement")
        decrement_button.onclick = decrement
        increment_button = self.modal_content.querySelector(".increment")
        increment_button.onclick = increment

        self.add_button = self.modal_content.querySelector(".add-btn")
        self.add_button.onclick = lambda event: self.add_to_cart(event, self.quantity)


class Cart(AbstractWidget):
    def __init__(self, element_id):
        AbstractWidget.__init__(self, element_id)
        self.orders = None
        self.username = fetch_user_info()
        self.fetch_orders_info()

    def fetch_orders_info(self):
        url = f"http://localhost:8000/users/{self.username}/orders"
        response = requests.get(url)
        if response.status_code == 200:
            self.orders = response.json()["orders"]
        else:
            print("Error fetching menu:", response.text)

    def drawWidget(self):
        items_container = ""
        for item in self.orders:
            items_container += f"""
                <div class="flex flex-row justify-center items-center gap-10">
                    <img class="w-36 w-36 mb-1" src="https://img.freepik.com/free-vector/illustration-gallery-icon_53876-27002.jpg" />
                    <div class="flex flex-col w-1/2">
                        <h3 class="capitalize text-base sm:text-lg">{item['name']}</h3>
                        <p class="text-sm">฿ {item['price']}</p>
                        <p class="text-sm">x{item['quantity']}</p>
                    </div>
                </div>
            """

        content = document.createElement("div")
        content.innerHTML = f"""
            <div class="flex flex-col justify-center items-center text-white gap-8 py-4">
                <div class="text-4xl">
                    Cart
                </div>
                <div class="w-full flex flex-col gap-4">
                    {items_container}
                </div>
                <div class="bg-zinc-700 rounded-full p-8 cursor-pointer">
                    Place Order
                </div>
            </div>
        """
        self.element.appendChild(content)


if __name__ == "__main__":
    location_path = js.window.location.pathname

    Navbar("app").drawWidget()

    content = Layout("app")
    if location_path == "/":
        content.drawWidget([Welcome("content")])
    elif location_path in ["/login", "/admin_login"]:
        content.drawWidget([Login("content")])
    elif location_path in ["/register", "/admin_register"]:
        content.drawWidget([Register("content")])
    elif location_path == "/home":
        content.drawWidget([Home("content")])
    elif location_path == "/menu":
        content.drawWidget([Menu("content")])
    elif location_path == "/cart":
        content.drawWidget([Cart("content")])
    else:
        content.drawWidget([NotFound("content")])
