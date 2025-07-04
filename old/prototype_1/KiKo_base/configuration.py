"""
This scenario demonstrates implementing BSPL agents using Python decorators.
For an alternative approach using AgentSpeak (ASL), see the grading scenario.
Both approaches are valid and used throughout the project:
- ASL files (like in grading/) are better for complex rule-based behavior
- Python decorators (used here) are simpler for straightforward request-response patterns
"""

import bspl

buy = bspl.load_file("buy.bspl").export("Buy")
from Buy import Buyer, Seller

negotiate = bspl.load_file("negotiate.bspl").export("Negotiate")
from Negotiate import B, S

agents = {
    "Seller": [("127.0.0.1", 8004)],
    "Buyer": [("127.0.0.1", 8005)]
}

systems = {
    "buy": {
        "protocol": buy,
        "roles": {
            Buyer: "Buyer",
            Seller: "Seller"
        }
    }
}
