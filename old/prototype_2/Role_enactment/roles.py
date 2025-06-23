import bspl


buy = bspl.load_file("buy.bspl").export("Buy")
from Buy import Buyer, Seller

print(buy.roles['Buyer'].dependencies)