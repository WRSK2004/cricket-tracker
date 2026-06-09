# =======================================================================
# app.py
# Flask RESTAPI server.
# Two Endpoints exposed:
# 
# POST /analyse - Accepts a video file, runs the pose estimation and 
#                 stance analysis pipeline, results are stored in Firestore and 
#                 feedback is returned.
#
# POST /health - Accepts user health data and returns calculated BMI,
#                BMR, TDEE, macronutrient targets and calorie targets.
# =======================================================================

# ---- Imports ----
from flask import Flask, request, jsonify
from flask_cors import CORS
from firebase_admin_setup import db, bucket
import os
import tempfile
import cv2
import subprocess

from core.frame_selector import select_best_frame
from core.pose_extractor import extract_landmarks
from core.stance_rules import analyse_stance
from core.anonymise import anonymise_video, anonymise_frame
from core.feedback import generate_feedback

# ---- Flask App Initialization ----
app = Flask(__name__)
CORS(app)

# ---- ENDPOINT: /analyse ----
@app.route('/analyse', methods=['POST'])
def analyse():
    # A video file undergos the following pipeline:
    # 1: Convert to MP4 with H.264 Codec for Compatibility
    # 2: Select Best Frame for Pose Analysis
    # 3: Extract Pose Landmarks
    # 4: Analyse Stance and Generate Feedback
    # 5: Anonymise Best Frame and Upload to Firebase Storage
    # 6: Anonymise Video and Upload to Firebase Storage
    # 7: Re-encode Anonymised Video to Ensure Compatibility
    # 8: Upload Anonymised Video to Firebase Storage and Serialise Results
    # 9: Store Analysis Results in Firestore
    # 10: Return Feedback and URLs in Response
    # If any step fails, an error message is returned. Temporary files are cleaned up after

    # ---- Validate Request ----
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # ---- Save Uploaded Video to Temporary File ----
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input_video:
        video_file.save(temp_input_video.name)
        temp_input_video_path = temp_input_video.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_output_video:
        temp_output_video_path = temp_output_video.name

    user_id = request.headers.get('X-User-ID', 'anonymous')

    temp_frame_path = None
    temp_converted_video_path = None
    temp_anonymised_video_path = None

    try:
        # ---- 1: Convert to MP4 with H.264 Codec for Compatibility ----
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_converted_video:
            temp_converted_video_path = temp_converted_video.name
            subprocess.run([
                "ffmpeg", "-y",
                "-i", temp_input_video_path,
                "-vcodec", "libx264",
                "-pix_fmt", "yuv420p",
                "-acodec", "aac",
                "-movflags", "+faststart",
                temp_converted_video_path
            ], check=True)

        # ---- 2: Select Best Frame for Pose Analysis ----
        best_frame = select_best_frame(temp_converted_video_path, 1, 2)
        
        if best_frame is None:
            return jsonify({"error": "Could not process video frames"}), 400
        
        best_frame, frame_num, visibility = best_frame

        # ---- 3: Extract Pose Landmarks ----
        landmarks = extract_landmarks(best_frame)
        if landmarks is None:
            return jsonify({"error": "Could not extract pose landmarks"}), 400
        
        # ---- 4: Analyse Stance and Generate Feedback ----
        rule_results = analyse_stance(landmarks)
        feedback = generate_feedback(rule_results)

        # ---- 5: Anonymise Best Frame and Upload to Firebase Storage ----
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_frame:
            temp_frame_path = temp_frame.name

        anonymised_best_frame = anonymise_frame(best_frame, rule_results)
        cv2.imwrite(temp_frame_path, anonymised_best_frame)

        frame_blob = bucket.blob(f"best_frames/{user_id}/{frame_num}.jpg")
        frame_blob.upload_from_filename(temp_frame_path)
        frame_blob.make_public()
        best_frame_url = frame_blob.public_url
        
        # ---- 6: Anonymise Video and Upload to Firebase Storage ----
        anonymise_video(temp_converted_video_path, temp_output_video_path, rule_results)
        
        # ---- 7: Re-encode Anonymised Video to Ensure Compatibility ----
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_anonymised_video:
            temp_anonymised_video_path = temp_anonymised_video.name
            
        subprocess.run([
            "ffmpeg", "-y",
            "-i", temp_output_video_path,
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            temp_anonymised_video_path
        ], check=True)

        # ---- 8: Upload Anonymised Video to Firebase Storage and Serialise Results ----
        blob = bucket.blob(f"anonymised/{user_id}/{frame_num}.mp4")
        blob.upload_from_filename(temp_anonymised_video_path)
        blob.make_public()
        video_url = blob.public_url

        serialised_results = {
            k: {key: val for key, val in v.items() if key != "colour"}
            for k, v in rule_results.items()
        }

        # ---- 9: Store Analysis Results in Firestore ----
        doc_ref = db.collection('analyses').document()
        doc_ref.set({
            'user_id': user_id,
            'video_url': video_url,
            'frame_number': frame_num,
            'visibility': float(visibility),
            'rule_results': serialised_results,
            'feedback': feedback
        })
        
        # ---- 10: Return Feedback and URLs in Response ----
        return jsonify({
            "feedback": feedback,
            "results": serialised_results,
            "video_url": video_url,
            "best_frame_url": best_frame_url,
            "frame_number": frame_num,
            "visibility": float(visibility)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        # ---- Clean Up Temporary Files ----
        if os.path.exists(temp_input_video_path):
            os.remove(temp_input_video_path)
        if os.path.exists(temp_output_video_path):
            os.remove(temp_output_video_path)
        if temp_frame_path and os.path.exists(temp_frame_path):
            os.remove(temp_frame_path)
        if temp_converted_video_path and os.path.exists(temp_converted_video_path):
            os.remove(temp_converted_video_path)
        if temp_anonymised_video_path and os.path.exists(temp_anonymised_video_path):
            os.remove(temp_anonymised_video_path)

# --- ENDPOINT: /health ----
@app.route('/health', methods=['POST'])
def health():
    # The user's age, gender, height(cm), weight(kg) and activitiy level are taken
    # and the BMI, BMR, TDEE, macronutrients and calorie targets are calculated and returned. 
    # The Mifflin-St Jeor equation is used for calculating BMR.  

    # ---- Validate Request Data ----
    data = request.get_json()
    activity = data.get('activity')
    age = data.get('age')
    height = data.get('height')
    gender = data.get('gender')
    weight = data.get('weight')

    if not all([activity, age, height, gender, weight]):
        return jsonify({"error": "Missing required fields"}), 400

    if age == 0:
        return jsonify({"error": "Age cannot be zero"}), 400
    if height == 0:
        return jsonify({"error": "Height cannot be zero"}), 400
    if gender not in ['male', 'female']:
        return jsonify({"error": "Invalid gender value. Must be 'male' or 'female'."}), 400
    if weight == 0:
        return jsonify({"error": "Weight cannot be zero"}), 400

    # ---- Calculate BMI, BMR, TDEE, Macronutrients, and Calorie Targets ----
    BMI = weight / ((height / 100) ** 2)
    
    if gender == 'male':
        BMR = 10 * weight + 6.25 * height - 5 * age + 5
    elif gender == 'female':
        BMR = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        return jsonify({"error": "Invalid gender value. Must be 'male' or 'female'."}), 400

    activity_factors = {
        "sedentary": 1.2,
        "lightly active": 1.375,
        "moderately active": 1.55,
        "very active": 1.725,
        "extra active": 1.9
    }
    activity_factor = activity_factors.get(activity, 1.2)

    TDEE = BMR * activity_factor
    
    macronutrients = {
        "protein": round(0.3 * TDEE / 4, 2),
        "carbohydrates": round(0.5 * TDEE / 4, 2),
        "fats": round(0.2 * TDEE / 9, 2)
    }

    maintenance_calories = round(TDEE, 2)
    weight_loss_calories = round(TDEE - 500, 2)
    weight_gain_calories = round(TDEE + 500, 2)

    return jsonify({
        "BMI": round(BMI, 2),
        "BMR": round(BMR, 2),
        "TDEE": round(TDEE, 2),
        "macronutrients": macronutrients,
        "maintenance_calories": maintenance_calories,
        "weight_loss_calories": weight_loss_calories,
        "weight_gain_calories": weight_gain_calories
    })

# ---- Run Flask App ----
if __name__ == '__main__':
    app.run(debug=True)