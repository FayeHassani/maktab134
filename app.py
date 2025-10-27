from abc import ABC, abstractmethod

class Product(ABC):
    identifier= 10000
    def __init__(self, name, brand, category, price, stock, detail = None, discount= None):
        self.name = name
        self.brand = brand
        self.category = category
        self.price = price
        self.detail = detail
        self.discount = discount
        self.stock = stock
        self.identifier += 1


    @abstractmethod
    def discount(self, percentage):
        pass


class Cart(ABC):
    cart=
    def __init__(self):
        pass

    @abstractmethod
    def add_to_cart(self, product):
        if isinstance(product, Product):
            if self.stock != 0:
                self.cart.append(product)
                self.stock -= 1
            raise ValueError ("Out of stock!")
        raise ValueError ("Please choose from products.")
        

    @abstractmethod
    def remove_from_cart(self, product):
        if product in self.cart:
            self.cart.remove(product)
        raise ValueError ("This item in not in your cart.")


    @abstractmethod
    def cart_discount(self, percentage = None):
        if percentage:
            self.price = self.price * (100- percentage) /100 
        else:
            pass


    @abstractmethod
    def cal_total(self):
        total = sum(item.price for item in self.cart)
        print(f"The total price is {total}") 
        
    @abstractmethod
    def show_items(self):
        print(f"You added these items to your cart: {self.cart}")

class ManageCart:
    carts = []
    def __init__(self, cart):
        if isinstance(cart, Cart):
            ManageCart.carts.append(cart)
        raise ValueError ("The cart is not defined!")
    
    def totol_carts(self):
        total_carts = sum(self.cart for cart in ManageCart )

    
    def total_price(self):
        total_price = sum(self.total for cart in ManageCart)

    
    def show_cart(self):
        print(f"Your carts contains these carts : {ManageCart.carts}")




