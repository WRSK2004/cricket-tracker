# =======================================================================
# health_metrics.py
# The user's age, sex, height (cm), weight (kg) and activity level are
# taken and the BMI, BMR, TDEE, macronutrients and calorie targets are
# calculated. The Mifflin-St Jeor equation is used for calculating BMR.
# Kept free of web/framework code so it can be unit tested directly.
# =======================================================================

# ---- Activity Multipliers (applied to BMR to get TDEE) ----
ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "lightly active": 1.375,
    "moderately active": 1.55,
    "very active": 1.725,
    "extra active": 1.9,
}


# ---- Calculate BMI, BMR, TDEE, Macronutrients, and Calorie Targets ----
def calculate_health_metrics(age, sex, height_cm, weight_kg, activity):
    if sex not in ("male", "female"):
        raise ValueError("sex must be 'male' or 'female'")
    if activity not in ACTIVITY_FACTORS:
        raise ValueError(f"activity must be one of {list(ACTIVITY_FACTORS)}")

    bmi = weight_kg / ((height_cm / 100) ** 2)

    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age
    bmr += 5 if sex == "male" else -161

    tdee = bmr * ACTIVITY_FACTORS[activity]

    macronutrients = {
        "protein": round(0.3 * tdee / 4, 2),
        "carbohydrates": round(0.5 * tdee / 4, 2),
        "fats": round(0.2 * tdee / 9, 2),
    }

    return {
        "BMI": round(bmi, 2),
        "BMR": round(bmr, 2),
        "TDEE": round(tdee, 2),
        "macronutrients": macronutrients,
        "maintenance_calories": round(tdee, 2),
        "weight_loss_calories": round(tdee - 500, 2),
        "weight_gain_calories": round(tdee + 500, 2),
    }
