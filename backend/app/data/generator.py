import random
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
import yaml

from app.core.config import config

class NovaMartDataGenerator:
    """
    Deterministic Synthetic Data Generator for NovaMart.
    Generates 3 heterogeneous data sources across 90 days with known, internally consistent scenarios.
    """
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        random.seed(seed)

        # Catalog definitions
        self.categories = {
            "Electronics": [
                {"product_id": "PROD_LAPTOP_01", "name": "UltraBook Pro 15", "base_price": 1299.00, "base_cost": 720.00, "weight": 0.20},
                {"product_id": "PROD_PHONE_01", "name": "NovaPhone 12", "base_price": 899.00, "base_cost": 500.00, "weight": 0.30},
                {"product_id": "PROD_HEADPHONES_01", "name": "NoiseCancel Wireless", "base_price": 199.00, "base_cost": 85.00, "weight": 0.30},
                {"product_id": "PROD_ACCESSORY_01", "name": "USB-C Multi-Hub", "base_price": 45.00, "base_cost": 15.00, "weight": 0.20},
            ],
            "Apparel": [
                {"product_id": "PROD_JACKET_01", "name": "All-Weather Parka", "base_price": 180.00, "base_cost": 75.00, "weight": 0.25},
                {"product_id": "PROD_SHOES_01", "name": "CloudRunning Sneakers", "base_price": 130.00, "base_cost": 50.00, "weight": 0.35},
                {"product_id": "PROD_TSHIRT_01", "name": "Organic Cotton Tee", "base_price": 35.00, "base_cost": 10.00, "weight": 0.40},
            ],
            "Home & Kitchen": [
                {"product_id": "PROD_BLENDER_01", "name": "NutriBlend Max 1000W", "base_price": 120.00, "base_cost": 55.00, "weight": 0.45},
                {"product_id": "PROD_COFFEE_01", "name": "Artisan Espresso Maker", "base_price": 250.00, "base_cost": 110.00, "weight": 0.55},
            ],
            "Beauty": [
                {"product_id": "PROD_SERUM_01", "name": "HydraGlow Vitamin C Serum", "base_price": 58.00, "base_cost": 14.00, "weight": 0.50},
                {"product_id": "PROD_CREAM_01", "name": "Night Repair Moisturizer", "base_price": 48.00, "base_cost": 12.00, "weight": 0.50},
            ],
        }

        self.regions = ["NA", "EU", "APAC"]
        self.region_weights = [0.45, 0.35, 0.20]

        self.channels = ["Search", "Social", "Influencer", "Email"]
        self.channel_base_cvr = {
            "Search": 0.034,
            "Social": 0.022,
            "Influencer": 0.012,
            "Email": 0.048,
        }

        # Date parameters: 90 days ending on 2026-08-28
        self.end_date = date(2026, 8, 28)
        self.start_date = self.end_date - timedelta(days=89)
        self.anomaly_start_date = date(2026, 8, 22)

    def generate_scenario_data(self, scenario_id: str = "SCENARIO_1_MULTI_FACTOR") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Generates the 3 heterogeneous sources for the specified scenario.
        Returns: (sales_df, marketing_df, customer_ops_df, metadata)
        """
        # Re-seed for reproducibility per scenario
        self.rng = np.random.default_rng(self.seed)
        random.seed(self.seed)

        if scenario_id == "SCENARIO_4_SPARSE_HISTORY":
            # Sparse history: only 5 days
            cur_start_date = self.end_date - timedelta(days=4)
        else:
            cur_start_date = self.start_date

        num_days = (self.end_date - cur_start_date).days + 1
        date_list = [cur_start_date + timedelta(days=i) for i in range(num_days)]

        sales_records = []
        marketing_records = []
        ops_records = []

        for current_date in date_list:
            is_anomaly = (current_date >= self.anomaly_start_date)
            
            # --- 1. MARKETING SOURCE GENERATION (Hourly / Daily grain) ---
            for region in self.regions:
                for channel in self.channels:
                    base_spend = 1200 if channel == "Search" else (800 if channel == "Social" else 400)
                    base_cpc = 0.85 if channel == "Search" else (0.50 if channel == "Social" else 0.35)
                    
                    spend = base_spend * (1.0 + self.rng.normal(0, 0.05))
                    cpc = base_cpc * (1.0 + self.rng.normal(0, 0.03))
                    
                    clicks = int(spend / cpc)
                    impressions = int(clicks * (25 + self.rng.normal(0, 2)))
                    cvr = self.channel_base_cvr[channel] * (1.0 + self.rng.normal(0, 0.04))

                    # Inject Scenario-specific marketing dynamics
                    if is_anomaly:
                        if scenario_id == "SCENARIO_1_MULTI_FACTOR":
                            # Driver 3: Marketing shift - Search spend cut by 45%, reallocated to low-cvr Social
                            if channel == "Search":
                                spend *= 0.55
                                clicks = int(clicks * 0.55)
                            elif channel == "Social":
                                spend *= 1.40
                                clicks = int(clicks * 1.35)
                                cvr *= 0.80 # Traffic quality dip
                            
                            # Driver 1: EU Conversion rate drop (due to payment gateway failure)
                            if region == "EU":
                                cvr *= 0.62 # 38% conversion drop in EU
                        
                        elif scenario_id == "SCENARIO_2_HIGH_CONFIDENCE":
                            # Search campaign accident pause
                            if channel == "Search":
                                spend = 0.0
                                clicks = 0
                                impressions = 0
                                cvr = 0.0

                    conversions = int(clicks * cvr)

                    marketing_records.append({
                        "date": current_date.isoformat(),
                        "campaign_id": f"CAMP_{channel.upper()}_{region}",
                        "channel": channel,
                        "region": region,
                        "spend": round(float(spend), 2),
                        "impressions": int(impressions),
                        "clicks": int(clicks),
                        "conversions": int(conversions),
                    })

            # --- 2. SALES SOURCE GENERATION (Transaction/Product/Day grain) ---
            # Total orders for the day across regions
            day_mkt = [m for m in marketing_records if m["date"] == current_date.isoformat()]
            total_day_conversions = sum(m["conversions"] for m in day_mkt)

            # Generate order line items
            order_counter = 0
            for region, r_weight in zip(self.regions, self.region_weights):
                region_conversions = int(total_day_conversions * r_weight)
                
                for _ in range(region_conversions):
                    order_counter += 1
                    order_id = f"ORD-{current_date.strftime('%Y%m%d')}-{region}-{order_counter:04d}"
                    
                    # Choose category
                    category = self.rng.choice(list(self.categories.keys()), p=[0.35, 0.30, 0.20, 0.15])
                    product_choices = self.categories[category]
                    weights = [p["weight"] for p in product_choices]
                    
                    # Scenario 1: Laptop Out of Stock in NA (Driver 2: Mix Shift)
                    if is_anomaly and scenario_id == "SCENARIO_1_MULTI_FACTOR":
                        if region == "NA" and category == "Electronics":
                            # UltraBook Pro is out of stock -> force purchase to USB-C Multi-Hub accessory or headphones
                            weights = [0.0, 0.35, 0.35, 0.30]
                    
                    product = self.rng.choice(product_choices, p=weights)
                    qty = 1 if product["base_price"] > 200 else int(self.rng.choice([1, 2], p=[0.8, 0.2]))
                    unit_price = product["base_price"]
                    unit_cost = product["base_cost"]

                    # Base discount
                    discount_rate = 0.05 + float(self.rng.uniform(0.0, 0.05))

                    # Scenario 5: Discount Spike in Apparel
                    if is_anomaly and scenario_id == "SCENARIO_5_CONTRADICTORY_EVIDENCE":
                        if category == "Apparel":
                            discount_rate = 0.22 # Unapproved 22% coupon code

                    line_revenue = unit_price * qty
                    line_discount = line_revenue * discount_rate
                    line_cost = unit_cost * qty

                    sales_records.append({
                        "date": current_date.isoformat(),
                        "order_id": order_id,
                        "product_id": product["product_id"],
                        "category": category,
                        "region": region,
                        "quantity": int(qty),
                        "revenue": round(float(line_revenue), 2),
                        "discount": round(float(line_discount), 2),
                        "cost": round(float(line_cost), 2),
                    })

            # --- 3. CUSTOMER & OPERATIONS UNSTRUCTURED EVENTS GENERATION ---
            # Baseline ticket noise (2-4 random normal tickets/reviews per day)
            num_noise_tickets = int(self.rng.integers(2, 5))
            for _ in range(num_noise_tickets):
                ops_records.append({
                    "timestamp": f"{current_date.isoformat()}T{self.rng.integers(8, 20):02d}:{self.rng.integers(10, 59):02d}:00Z",
                    "source": self.rng.choice(["SUPPORT_TICKET", "CUSTOMER_REVIEW"]),
                    "region": self.rng.choice(self.regions),
                    "product_id": self.rng.choice(["PROD_PHONE_01", "PROD_JACKET_01", "PROD_BLENDER_01"]),
                    "category": "General",
                    "sentiment": round(float(self.rng.uniform(0.2, 0.8)), 2),
                    "text": "Product arrived promptly, packaging in good condition.",
                    "issue_type": "GENERAL_INQUIRY",
                    "severity": "LOW",
                    "sensitivity": "PUBLIC_FEEDBACK",
                })

            # Inject Scenario-specific Unstructured Evidence
            if is_anomaly:
                if scenario_id == "SCENARIO_1_MULTI_FACTOR":
                    # Injected Evidence for Cause 1: EU Checkout Gateway Timeout (45 tickets over the 7-day window)
                    for _ in range(7):
                        ops_records.append({
                            "timestamp": f"{current_date.isoformat()}T{self.rng.integers(10, 18):02d}:{self.rng.integers(0, 59):02d}:00Z",
                            "source": "SUPPORT_TICKET",
                            "region": "EU",
                            "product_id": None,
                            "category": "Checkout",
                            "sentiment": -0.88,
                            "text": f"Customer in Berlin reported checkout error: 'Payment gateway timed out during 3D Secure verification on Adyen EU endpoint'.",
                            "issue_type": "PAYMENT_GATEWAY_TIMEOUT",
                            "severity": "CRITICAL",
                            "sensitivity": "PII_RESTRICTED",
                        })
                    
                    # 1 Ops Incident note on EU Adyen gateway
                    if current_date == self.anomaly_start_date:
                        ops_records.append({
                            "timestamp": f"{current_date.isoformat()}T09:15:00Z",
                            "source": "OPS_INCIDENT",
                            "region": "EU",
                            "product_id": None,
                            "category": "Payment_Gateway",
                            "sentiment": -0.95,
                            "text": "INCIDENT INC-8092: Adyen EU payment gateway latency spiked to 4850ms after TLS renegotiation patch. Checkout failure rate increased to 38%.",
                            "issue_type": "PAYMENT_GATEWAY_TIMEOUT",
                            "severity": "CRITICAL",
                            "sensitivity": "INTERNAL_OPS",
                        })

                    # Injected Evidence for Cause 2: NA Laptop Stockout (Mix Shift)
                    for _ in range(2):
                        ops_records.append({
                            "timestamp": f"{current_date.isoformat()}T14:30:00Z",
                            "source": "SUPPORT_TICKET",
                            "region": "NA",
                            "product_id": "PROD_LAPTOP_01",
                            "category": "Electronics",
                            "sentiment": -0.70,
                            "text": "Customer trying to purchase UltraBook Pro 15 received 'Out of Stock - Backorder in 3 weeks' alert at cart.",
                            "issue_type": "STOCKOUT",
                            "severity": "HIGH",
                            "sensitivity": "PII_RESTRICTED",
                        })

                    if current_date == self.anomaly_start_date:
                        ops_records.append({
                            "timestamp": f"{current_date.isoformat()}T06:00:00Z",
                            "source": "OPS_INCIDENT",
                            "region": "NA",
                            "product_id": "PROD_LAPTOP_01",
                            "category": "Inventory",
                            "sentiment": -0.75,
                            "text": "WMS LOG: North America East warehouse zero-inventory alert triggered for SKU PROD_LAPTOP_01 due to delayed inbound shipping container.",
                            "issue_type": "STOCKOUT",
                            "severity": "HIGH",
                            "sensitivity": "INTERNAL_OPS",
                        })

                elif scenario_id == "SCENARIO_2_HIGH_CONFIDENCE":
                    # Corroborating Campaign Log
                    ops_records.append({
                        "timestamp": f"{current_date.isoformat()}T08:00:00Z",
                        "source": "OPS_INCIDENT",
                        "region": "NA",
                        "product_id": None,
                        "category": "Marketing_Ops",
                        "sentiment": -0.90,
                        "text": "Marketing Ops Log: Google Ads Search Campaign CAMP_SEARCH_NA was accidentally paused during automated script migration.",
                        "issue_type": "CAMPAIGN_OUTAGE",
                        "severity": "HIGH",
                        "sensitivity": "INTERNAL_OPS",
                    })

                elif scenario_id == "SCENARIO_5_CONTRADICTORY_EVIDENCE":
                    # Ops note asserting carrier fuel surcharge (contradicting sales discount reality)
                    ops_records.append({
                        "timestamp": f"{current_date.isoformat()}T11:00:00Z",
                        "source": "OPS_INCIDENT",
                        "region": "EU",
                        "product_id": None,
                        "category": "Logistics",
                        "sentiment": -0.80,
                        "text": "Logistics Carrier Memo: DHL International imposed a 15% emergency fuel surcharge on cross-border EU freight, impacting line item margins.",
                        "issue_type": "SHIPPING_SURCHARGE",
                        "severity": "HIGH",
                        "sensitivity": "INTERNAL_OPS",
                    })

        sales_df = pd.DataFrame(sales_records)
        marketing_df = pd.DataFrame(marketing_records)
        customer_ops_df = pd.DataFrame(ops_records)

        metadata = {
            "scenario_id": scenario_id,
            "generated_at": datetime.now().isoformat(),
            "start_date": cur_start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "anomaly_start_date": self.anomaly_start_date.isoformat(),
            "sales_record_count": len(sales_df),
            "marketing_record_count": len(marketing_df),
            "customer_ops_record_count": len(customer_ops_df),
        }

        return sales_df, marketing_df, customer_ops_df, metadata

# Singleton instance
data_generator = NovaMartDataGenerator()
