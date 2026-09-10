import json

def load_power_data(json_path="data/power_rates.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_savings(survey_results: dict, json_path="data/power_rates.json"):
    data = load_power_data(json_path)
    unit_price = data["unit_price_krw"]
    emission_factor = data["emission_factor_kg_co2"]
    specs = data["equipment_specs"]
    
    total_kwh_min = 0.0
    total_kwh_max = 0.0
    
    if survey_results.get("ice_maker_filter", False):
        kw = specs["ice_maker"]["default_kw"]
        hours = specs["ice_maker"]["daily_operation_hours"] * 30
        monthly_consumption = kw * hours
        total_kwh_min += monthly_consumption * 0.10
        total_kwh_max += monthly_consumption * 0.15

    if survey_results.get("standby_power", False):
        kw = specs["coffee_machine"]["default_kw"] + specs["water_heater"]["default_kw"]
        hours = 8 * 30
        monthly_consumption = kw * hours
        total_kwh_min += monthly_consumption * 0.05
        total_kwh_max += monthly_consumption * 0.10

    cost_min = int(total_kwh_min * unit_price)
    cost_max = int(total_kwh_max * unit_price)
    carbon_min = round(total_kwh_min * emission_factor, 1)
    carbon_max = round(total_kwh_max * emission_factor, 1)

    return {
        "kwh_range": (round(total_kwh_min, 1), round(total_kwh_max, 1)),
        "cost_range": (cost_min, cost_max),
        "carbon_range": (carbon_min, carbon_max)
    }
