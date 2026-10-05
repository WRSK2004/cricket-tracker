// =====================================================================
// Title: healthTracker.js
// This JavaScript handles the 'Health & Fitness' page.
// Main Functionalities:
// - Calculate Health Metrics - sends age, gender, height, weight, and
//   activity level to the backend /health endpoint and the BMI, BMR, TDEE,
//   and macronutrient distribution are returned, saved to Firestore, 
//   and displayed to the user.
// - Calculate Target Calories and Weekly Plan - based on the health metrics,
//   target weight, and weight change per week, the target calories and a
//   weekly calorie plan are generated, displayed, and visualised in a chart.
// =====================================================================

// ---- Authenticated API Calls ----
import { apiFetch } from "../../utils/api.js";

// ---- Firebase Imports ----
import { doc, setDoc } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

// ---- Shared Firebase Instances ----
import { auth, db } from "../../utils/firebase.js";

// ---- Global Variables/Module State ----
let healthResult = null;
let calorieChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    // ---- Collapsible Information Section ----
    document.querySelector('.collapsible-information-button').addEventListener('click', () => {
    const content = document.querySelector('.information-content');
    const isOpen = content.style.display === 'block';
    content.style.display = isOpen ? 'none' : 'block';
    });
    
    // ---- Calculate Health Metrics and Target Calories ----
    document.getElementById('calculate-health-metrics').addEventListener('click', async () => {
        const age = parseInt(document.getElementById('age').value);
        const gender = document.getElementById('gender').value;
        const height = parseFloat(document.getElementById('height').value);
        const weight = parseFloat(document.getElementById('weight').value);
        const activityLevel = document.getElementById('activity-levels').value;

        // ---- Input Validation ----
        if (isNaN(age) || gender === "" || isNaN(height) || isNaN(weight) || activityLevel === "") {
            alert("Please enter valid numbers for age, height, and weight, and select a gender and activity level.");
            return;
        }

        // ---- Send to the Backend /health Endpoint for Calculation ----
        try {
            healthResult = await apiFetch('/health', {
                method: 'POST',
                body: { age, gender, height, weight, activity: activityLevel }
            });
        } catch (error) {
            alert(error.message);
            return;
        }
        displayHealthResults(healthResult);

        return healthResult;
    });

    // ---- Calculate Target Calories and Weekly Plan ----
    document.getElementById('calculate-target-calories').addEventListener('click', () => {
        if (!healthResult) {
            alert("Please calculate your health metrics first.");
            return;
        }

        const targetWeight = parseFloat(document.getElementById('target-weight').value);
        const weightPerWeek = parseFloat(document.getElementById('weight-per-week').value);
        const currentWeight = parseFloat(document.getElementById('weight').value);
        const isWeightGain = targetWeight > currentWeight;

        // ---- Input Validation ----
        if (isNaN(targetWeight) || isNaN(weightPerWeek)) {
            alert("Please enter valid numbers for target weight and weight change per week.");
            return;
        }

        const today = new Date();
        let targetDate = new Date(today);
        const weeksNeeded = Math.ceil(Math.abs(currentWeight - targetWeight) / weightPerWeek);
        targetDate.setDate(today.getDate() + weeksNeeded * 7);

        document.getElementById('target-date-info').innerHTML = `
            Target Completion Date: ${targetDate.toDateString()}<br>
            Weeks Needed: ${weeksNeeded} week(s)
        `;

        // ---- Generate Weekly Calorie Plan ----
        let weeklyPlan = [];

        let currentCalories = isWeightGain ?
            healthResult.weight_gain_calories :
            healthResult.weight_loss_calories;

        const weeklyPlanList = document.getElementById('weekly-plan');
        weeklyPlanList.innerHTML = "";
        for (let i = 1; i <= weeksNeeded; i++){
            weeklyPlan.push(Math.round(currentCalories));
            weeklyPlanList.innerHTML += `<li>Week ${i}: ${Math.round(currentCalories)} calories/day</li>`;
        }

        // ---- 'Show/Hide' Button for Weekly Plan if More than 4 Weeks ----
        const showMoreButton = document.getElementById('show-more-button');
        if (weeksNeeded > 4){
            showMoreButton.style.display = 'block';
            showMoreButton.textContent = 'Show More';
            document.getElementById('weekly-plan').classList.add('collapsed');

            showMoreButton.onclick = () => {
                const list = document.getElementById('weekly-plan');
                list.classList.toggle('collapsed');
                showMoreButton.textContent = list.classList.contains('collapsed') ? 'Show More' : 'Show Less';
            };
        }
        else{
            showMoreButton.style.display = 'none';
        }

        drawChart(weeklyPlan);
        document.getElementById('target-calories-result').style.display = 'block';
    });

});

// ---- Display Health Metrics and Save to Firestore ----
async function displayHealthResults(result){
    // ---- Show Results Panel ----
    document.getElementById('results-placeholder').style.display = 'none';
    document.getElementById('health-metrics-results').style.display = 'block';
    
    // ---- Populate Results ----
    document.getElementById('bmi-result').textContent = `BMI: ${result.BMI.toFixed(2)}`;
    document.getElementById('bmi-category').textContent = `BMI Category: ${getBMICategory(result.BMI)}`;
    document.getElementById('bmr-result').textContent = `BMR: ${result.BMR.toFixed(2)} calories/day`;
    document.getElementById('tdee-result').textContent = `TDEE: ${result.TDEE.toFixed(2)} calories/day`;
    document.getElementById('macronutrient-distribution').innerHTML = `
        <p><strong>Macronutrient Distribution:</strong></p>
        <ul>
            <li>Carbohydrates: ${result.macronutrients.carbohydrates} grams/day</li>
            <li>Protein: ${result.macronutrients.protein} grams/day</li>
            <li>Fats: ${result.macronutrients.fats} grams/day</li>
        </ul>
        <p><strong>Maintenance Calories:</strong> ${result.maintenance_calories} calories/day</p>
        <p><strong>To lose weight:</strong> ${result.weight_loss_calories} calories/day</p>
        <p><strong>To gain weight:</strong> ${result.weight_gain_calories} calories/day</p>
    `;

    // ---- Save Health Metrics to Firestore ----
    const user = auth.currentUser;
    if (user) {
        await setDoc(doc(db, "users", user.uid), {
            healthMetrics: {
                BMI: result.BMI,
                BMR: result.BMR,
                TDEE: result.TDEE,
                maintenance_calories: result.maintenance_calories,
                weight_loss_calories: result.weight_loss_calories,
                weight_gain_calories: result.weight_gain_calories,
                macronutrients: result.macronutrients,
                lastCalculated : new Date().toLocaleDateString('en-GB')
            }
        }, { merge: true });
    }
}

// ---- BMI Category Helper Function ----
function getBMICategory(bmi){
    if (bmi < 18.5){
        return "Underweight";
    }
    else if (bmi >= 18.5 && bmi < 25){
        return "Normal weight";
    }
    else if (bmi >= 25 && bmi < 30){
        return "Overweight";
    }
    else {
        return "Obese";
    }
}

// ---- Chart Drawing Function ----
function drawChart(weeklyPlan){
    const ctx = document.getElementById('calorieChart').getContext('2d');
    // ---- Destroy existing chart instance ----
    if (calorieChartInstance) {
        calorieChartInstance.destroy();
    }

    calorieChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                    label: 'Target Calories',
                    data: [],
                    backgroundColor: '#74cc00',
                    borderColor: '#457a00',
                    borderWidth: 1
                }]
        },
        options: getChartOptions('Weekly Calorie Targets')
    });

    const labels = weeklyPlan.map((_, index) => `Week ${index + 1}`);
    calorieChartInstance.data.labels = labels;
    calorieChartInstance.data.datasets[0].data = weeklyPlan;
    calorieChartInstance.update();
}

// ---- Chart Options Helper Function ----
function getChartOptions(title) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            title: {
                display: true,
                text: title,
                font: {
                    size: 18
                }
            },
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Week',
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Calories (kcal)',
                }
            }
        }
    };
}