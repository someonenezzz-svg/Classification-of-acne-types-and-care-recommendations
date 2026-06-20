from flask import Flask, render_template, request, session, redirect, url_for
import requests
import os
app = Flask(__name__)
app.secret_key = "my_super_secret_key_for_acne_app"
EI_API_KEY = "YOUR_EDGE_IMPULSE_API_KEY"
EI_PROJECT_ID = "YOUR_PROJECT_ID"
EI_URL = f"https://studio.edgeimpulse.com/v1/api/{EI_PROJECT_ID}/inference" #เปลี่ยนใส่ของตัวเอง

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/train")
def train():
    return render_template("train.html")

@app.route("/form",methods=["GET", "POST"])
def form():
    if request.method == "POST":
        sex = request.form.get("choice")
        age = request.form.get("choice2")
        file = request.files.get("acne_image")
        acne_percentages = {}

        edge_scores = {
            "eat": 0,    # ก
            "hor": 0,    # ฮ
            "lif": 0,    # พ
            "cle": 0     # ส
        }

        if sex: session['sex'] = sex
        if age: session['age'] = age

        if file and file.filename != '':
            try:
                # อ่านไฟล์รูปเตรียมส่งแบบ binary
                files = {'data': (file.filename, file.read(), file.content_type)}
                headers = {
                    "x-api-key": EI_API_KEY,
                    "Accept": "application/json"
                }
                
                response = requests.post(EI_URL, headers=headers, files=files)
                
                if response.status_code == 200:
                    result_data = response.json()
                    bounding_boxes = result_data.get("results", [])
                    
                    valid_acnes = [box for box in bounding_boxes if box.get("value", 0) > 0.5]
                    total_acne_count = len(valid_acnes)
                    
                    if total_acne_count > 0:
                        acne_counts = {}
                        detected_labels = set()
                        for box in valid_acnes:
                            label = box.get("label", "Unknown")
                            acne_counts[label] = acne_counts.get(label, 0) + 1
                        
                        for label, count in acne_counts.items():
                            acne_percentages[label] = round((count / total_acne_count) * 100, 2)

                        for label in detected_labels:
                            if label in ["สิวขาว", "Whitehead"]:
                                edge_scores["eat"] += 16
                                edge_scores["hor"] += 20
                                edge_scores["lif"] += 12
                                edge_scores["cle"] += 18
                            elif label in ["สิวดำ", "Blackhead"]:
                                edge_scores["eat"] += 12
                                edge_scores["hor"] += 16
                                edge_scores["lif"] += 10
                                edge_scores["cle"] += 20
                            elif label in ["ตุ่มแดง", "Papule"]:
                                edge_scores["eat"] += 20
                                edge_scores["hor"] += 18
                                edge_scores["lif"] += 18
                                edge_scores["cle"] += 14
                            elif label in ["ตุ่มหนอง", "Pustule"]:
                                edge_scores["eat"] += 20
                                edge_scores["hor"] += 16
                                edge_scores["lif"] += 20
                                edge_scores["cle"] += 14
                            elif label in ["ซีสต์", "Cyst"]:
                                edge_scores["eat"] += 16
                                edge_scores["hor"] += 20
                                edge_scores["lif"] += 18
                                edge_scores["cle"] += 10

                    else:
                        acne_percentages = {"ไม่พบสิว หรือสภาพผิวปกติ": 100.0}

            except Exception as e:
                print(f"Error calling Edge Impulse API: {e}")
        
        session['acne_percentages'] = acne_percentages
        
        return render_template("form.html", sex=sex, age=age)
    
    return render_template("form.html")

@app.route("/result", methods=["POST"])
def result():
    sex = request.form.get("sex") 
    age = request.form.get("age")
    acne_results = session.get('acne_percentages', {})

    per_hor = per_cle = per_lif = per_eat = 0

    try:
        score_gender_specific = 0
        if sex == "1":
            score_gender_specific = int(request.form.get("choice0", 0)) 
        elif sex == "2":
            score_gender_specific = int(request.form.get("choice3", 0))

        score_age = float(request.form.get("choice2", 0))
        score_pillow = float(request.form.get("choice4", 0))      
        score_cleansing = int(request.form.get("choice5", 0))   
        score_sleep = float(request.form.get("choice6", 0))      
        score_touch = int(request.form.get("choice7", 0))       
        score_sweet = int(request.form.get("choice8", 0))       
        score_greasy = int(request.form.get("choice9", 0))

        score_all = score_age + score_gender_specific + score_pillow + score_cleansing + score_sleep + score_touch + score_sweet + score_greasy + edge_scores["eat"] + edge_scores["hor"] + edge_scores["lif"] + edge_scores["cle"]

        if score_all > 0:
            per_all = score_all/100
            sco_hor = score_age + score_gender_specific + edge_scores["hor"]
            per_hor = round((sco_hor / per_all), 2)
            sco_cle = score_pillow + score_cleansing + edge_scores["cle"]
            per_cle = round((sco_cle / per_all), 2)
            sco_lif = score_sleep + score_touch + edge_scores["lif"]
            per_lif = round((sco_lif / per_all), 2)
            sco_eat = score_sweet + score_greasy + edge_scores["eat"]
            per_eat = round((sco_eat / per_all), 2)


    except Exception as e:
        print(f" Error in calculation: {e}")   


    return render_template("result.html", 
                           acne_results=acne_results, 
                           per_hor=per_hor, 
                           per_cle=per_cle, 
                           per_lif=per_lif, 
                           per_eat=per_eat)
@app.route("/clear")
def clear_session():
    session.clear()
    return redirect(url_for("home"))
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0",port=8000)
    