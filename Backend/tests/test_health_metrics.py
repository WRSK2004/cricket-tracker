import pytest

from core.health_metrics import calculate_health_metrics


def test_male_example():
    # 25-year-old male, 180cm, 75kg, moderately active
    result = calculate_health_metrics(25, "male", 180, 75, "moderately active")
    assert result["BMI"] == pytest.approx(23.15, abs=0.01)
    assert result["BMR"] == pytest.approx(1755)  # 750 + 1125 - 125 + 5
    assert result["TDEE"] == pytest.approx(1755 * 1.55, abs=0.01)
    assert result["weight_loss_calories"] == pytest.approx(result["TDEE"] - 500, abs=0.01)


def test_female_offset():
    male = calculate_health_metrics(30, "male", 165, 60, "sedentary")
    female = calculate_health_metrics(30, "female", 165, 60, "sedentary")
    assert male["BMR"] - female["BMR"] == pytest.approx(166)


def test_macros_add_up_to_tdee():
    result = calculate_health_metrics(20, "female", 170, 65, "very active")
    macros = result["macronutrients"]
    kcal = macros["protein"] * 4 + macros["carbohydrates"] * 4 + macros["fats"] * 9
    assert kcal == pytest.approx(result["TDEE"], abs=1)


@pytest.mark.parametrize("sex,activity", [("other", "sedentary"), ("male", "couch")])
def test_invalid_inputs_rejected(sex, activity):
    with pytest.raises(ValueError):
        calculate_health_metrics(25, sex, 180, 75, activity)
