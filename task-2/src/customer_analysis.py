from datetime import datetime, timedelta
from typing import List, Dict
import json
from collections import defaultdict

# Sample data structures
class Customer:
    def __init__(self, customer_id: str, name: str, email: str):
        self.customer_id = customer_id
        self.name = name
        self.email = email

class Order:
    def __init__(self, order_id: str, customer_id: str, amount: float, category: str, date: datetime):
        self.order_id = order_id
        self.customer_id = customer_id
        self.amount = amount
        self.category = category
        self.date = date

# Sample data
customers = [
    Customer("C001", "John Smith", "john@email.com"),
    Customer("C002", "Emma Wilson", "emma@email.com"),
    Customer("C003", "Michael Brown", "michael@email.com"),
    Customer("C004", "Sarah Davis", "sarah@email.com"),
    Customer("C005", "James Johnson", "james@email.com"),
    Customer("C006", "Lisa Anderson", "lisa@email.com"),
    Customer("C007", "David Miller", "david@email.com"),
    Customer("C008", "Emily Taylor", "emily@email.com"),
]

# Sample orders spanning the past year with various categories
categories = ["Electronics", "Clothing", "Home & Kitchen"]
orders = [
    # High-value customer (Gold tier)
    Order("O001", "C001", 1200.0, "Electronics", datetime.now() - timedelta(days=30)),
    Order("O002", "C001", 800.0, "Clothing", datetime.now() - timedelta(days=60)),
    Order("O003", "C001", 1500.0, "Home & Kitchen", datetime.now() - timedelta(days=90)),
    
    # Medium-value customer (Silver tier)
    Order("O004", "C002", 600.0, "Electronics", datetime.now() - timedelta(days=45)),
    Order("O005", "C002", 900.0, "Clothing", datetime.now() - timedelta(days=75)),
    Order("O006", "C002", 700.0, "Home & Kitchen", datetime.now() - timedelta(days=120)),
    
    # Low-value customer (Bronze tier)
    Order("O007", "C003", 300.0, "Electronics", datetime.now() - timedelta(days=15)),
    Order("O008", "C003", 400.0, "Clothing", datetime.now() - timedelta(days=45)),
    
    # Inactive customer
    Order("O009", "C004", 800.0, "Electronics", datetime.now() - timedelta(days=200)),
    Order("O010", "C004", 600.0, "Clothing", datetime.now() - timedelta(days=220)),
    
    # Very low spend customer (should be excluded)
    Order("O011", "C005", 200.0, "Electronics", datetime.now() - timedelta(days=30)),
    Order("O012", "C005", 250.0, "Clothing", datetime.now() - timedelta(days=60)),
    
    # High-frequency customer
    Order("O013", "C006", 400.0, "Electronics", datetime.now() - timedelta(days=10)),
    Order("O014", "C006", 350.0, "Clothing", datetime.now() - timedelta(days=20)),
    Order("O015", "C006", 450.0, "Home & Kitchen", datetime.now() - timedelta(days=30)),
    
    # Mixed category customer
    Order("O016", "C007", 700.0, "Electronics", datetime.now() - timedelta(days=40)),
    Order("O017", "C007", 600.0, "Clothing", datetime.now() - timedelta(days=50)),
    Order("O018", "C007", 800.0, "Home & Kitchen", datetime.now() - timedelta(days=60)),
    
    # Recent customer
    Order("O019", "C008", 900.0, "Electronics", datetime.now() - timedelta(days=5)),
]

def get_loyalty_tier(total_spent: float):
    if total_spent > 3000:
        return "Gold"
    elif total_spent >= 1000:
        return "Silver"
    else:
        return "Bronze"

def analyze_customers():
    customer_data = {}
    six_months_ago = datetime.now() - timedelta(days=180)
    
    # Initialize customer data
    for customer in customers:
        customer_data[customer.customer_id] = {
            "customerId": customer.customer_id,
            "name": customer.name,
            "email": customer.email,
            "totalSpent": 0.0,
            "orders": [],
            "categorySpend": defaultdict(float),
            "lastPurchaseDate": None,
            "isActive": False
        }
    
    # Process orders
    for order in orders:
        customer = customer_data[order.customer_id]
        customer["totalSpent"] += order.amount
        customer["orders"].append(order)
        customer["categorySpend"][order.category] += order.amount
        
        if customer["lastPurchaseDate"] is None or order.date > customer["lastPurchaseDate"]:
            customer["lastPurchaseDate"] = order.date
            
        if order.date >= six_months_ago:
            customer["isActive"] = True
    
    # Generate report
    report = []
    for customer_id, data in customer_data.items():
        if data["totalSpent"] < 500:  # Exclude low-spending customers
            continue
            
        # Calculate average order value
        avg_order_value = data["totalSpent"] / len(data["orders"])
        
        # Find favorite category (earliest alphabetically in case of ties)
        category_counts = defaultdict(int)
        for order in data["orders"]:
            category_counts[order.category] += 1
        
        max_count = max(category_counts.values())
        favorite_categories = [cat for cat, count in category_counts.items() if count == max_count]
        favorite_category = min(favorite_categories)  # Select earliest alphabetically
        
        report.append({
            "customerId": data["customerId"],
            "name": data["name"],
            "email": data["email"],
            "totalSpent": round(data["totalSpent"], 2),
            "averageOrderValue": round(avg_order_value, 2),
            "favoriteCategory": favorite_category,
            "loyaltyTier": get_loyalty_tier(data["totalSpent"]),
            "lastPurchaseDate": data["lastPurchaseDate"].strftime("%Y-%m-%d"),
            "isActive": data["isActive"],
            "categoryWiseSpend": dict(data["categorySpend"])
        })
    
    return report

if __name__ == "__main__":
    report = analyze_customers()
    print(json.dumps(report, indent=2)) 