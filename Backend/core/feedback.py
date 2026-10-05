# =======================================================================
# feedback.py
# Nautural language feedback is generated using the Claude API. The structured
# stance analysis results from stance_rules.py are taken and a friendly plain
# text coaching response is returned to the user.
# =======================================================================

# ---- Imports ----

import anthropic
from dotenv import load_dotenv

load_dotenv()

# ---- Feedback Generation ----
def generate_feedback(rule_results):
    try:
        summary = ""
        for check_name, result in rule_results.items():
            summary += f"{check_name}: {result['status']}\n"
            if result.get("measured") is not None:
                summary += f"  Measured: {result['measured']:.2f}\n"
            summary += f"  Feedback: {result['message']}\n\n"

        # ---- System Prompt for Feedback Generation ----
        system_prompt = (
            "You are a cricket coach. The user is a beginner at cricket. "
            "You are providing the user feedback on their batting stance based on the following checks. "
            "For each check, you should give encouraging plain English feedback based on the stance analysis results. "
            "If the check passed, give positive feedback. If the check failed, give constructive feedback on how "
            "to improve, referencing the measured value if available. "
            "Keep the tone friendly and supportive. Respond in plain text only. Do not use markdown formatting, "
            "headers (#), asterisks (**), or bullet points. "
            "Just provide the feedback in simple sentences. You can use emojis to make the feedback more engaging, "
            "but do not overuse them."
        )

        # ---- Claude API Call ----
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system = system_prompt,
            messages = [
                {"role": "user", "content": summary}
            ]
        )

        return message.content[0].text

    except Exception as e:
        print(f"Error generating feedback: {e}")
        return "An error occurred while generating feedback."

# ---- Test Case ----
if __name__ == "__main__":
    sample_results = {
        "Knee Angle Check": {
            "status": "Fail",
            "measured": 120.5,
            "message": "The knee angle is too small. Aim for an angle between 130 and 160 degrees."
        },
        "Back Posture Check": {
            "status": "Pass",
            "measured": 15.0,
            "message": "Good back posture with a small forward lean."
        }
    }
    feedback = generate_feedback(sample_results)
    print("Generated Feedback:")
    print(feedback)
