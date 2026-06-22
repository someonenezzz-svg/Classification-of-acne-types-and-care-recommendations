from flask import Flask, render_template, request, session, redirect, url_for
import requests
import os

app = Flask(__name__)

app.secret_key = "my_super_secret_key_for_acne_app"


EI_API_KEY = "ei_b1b1a85a460fdf6c4e951a34fb6dc0a34c155cd24139b7b8"
EI_PROJECT_ID = "1031060"
EI_URL = f"https://studio.edgeimpulse.com/v1/api/{EI_PROJECT_ID}/inference"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/train")
def train():
    return render_template("train.html")

@app.route("/form", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        sex = request.form.get("choice")
        age = request.form.get("choice2")
        file = request.files.get("acne_image")
        
        acne_percentages = {}
        
        edge_scores = {
            "eat": 0,    
            "hor": 0,    
            "lif": 0,    
            "cle": 0     
        }

        
        if sex:
            session['sex'] = sex
        if age: 
            session['age'] = float(age)

        
        if file and file.filename != '':
            try:
                file.seek(0)
                image_data = file.read()
                
                headers = {
                    "x-api-key": EI_API_KEY,
                    "Content-Type": file.mimetype if file.mimetype else "image/jpeg",
                    "Accept": "application/json"
                }
                
                try:
                    response = requests.post(EI_URL, data=image_data, headers=headers, timeout=10)
                    status_code = response.status_code
                except Exception:
                    status_code = 500

                if status_code == 200:
                    result_data = response.json()
                    
                   
                    bounding_boxes = []
                    if "results" in result_data:
                        bounding_boxes = result_data["results"]
                    elif "result" in result_data and "bounding_boxes" in result_data["result"]:
                        bounding_boxes = result_data["result"]["bounding_boxes"]
                    elif "bounding_boxes" in result_data:
                        bounding_boxes = result_data["bounding_boxes"]

                    
                    valid_acnes = [box for box in bounding_boxes if box.get("value", 0) > 0.5]
                    total_acne_count = len(valid_acnes)
                
                else:
                    
                    print(f"Edge Impulse API Error status: {status_code}")
                    valid_acnes = []
                    total_acne_count = 0

                
                if total_acne_count > 0:
                    acne_counts = {}
                    for box in valid_acnes:
                        label = box.get("label", "Unknown").strip().lower()
                        acne_counts[label] = acne_counts.get(label, 0) + 1
                    
                    acne_percentages = {}

                    
                    for label, count in acne_counts.items():
                        thai_label = label
                        if label == "white": thai_label = "สิวหัวขาว"
                        elif label == "black": thai_label = "สิวหัวดำ"
                        elif label == "papular": thai_label = "สิวตุ่มแดง"
                        elif label == "pustular": thai_label = "สิวตุ่มหนอง"
                        elif label == "cystic": thai_label = "สิวซีสต์"
                        acne_percentages[thai_label] = round((count / total_acne_count) * 100, 2)

                    
                    for label, count in acne_counts.items():
                        if label == "white":
                            edge_scores["eat"] += (16 * count)
                            edge_scores["hor"] += (20 * count)
                            edge_scores["lif"] += (12 * count)
                            edge_scores["cle"] += (18 * count)
                        elif label == "black":
                            edge_scores["eat"] += (12 * count)
                            edge_scores["hor"] += (16 * count)
                            edge_scores["lif"] += (10 * count)
                            edge_scores["cle"] += (20 * count)
                        elif label == "papular":
                            edge_scores["eat"] += (20 * count)
                            edge_scores["hor"] += (18 * count)
                            edge_scores["lif"] += (18 * count)
                            edge_scores["cle"] += (14 * count)
                        elif label == "pustular":
                            edge_scores["eat"] += (20 * count)
                            edge_scores["hor"] += (16 * count)
                            edge_scores["lif"] += (20 * count)
                            edge_scores["cle"] += (14 * count)
                        elif label == "cystic":
                            edge_scores["eat"] += (16 * count)
                            edge_scores["hor"] += (20 * count)
                            edge_scores["lif"] += (18 * count)
                            edge_scores["cle"] += (10 * count)

                else:
                    acne_percentages = {"ไม่พบสิว หรือสภาพผิวปกติ": 100.0}

            except Exception as e:
                print(f"Error calling Edge Impulse API: {e}")
                acne_percentages = {"ไม่พบสิว หรือสภาพผิวปกติ": 100.0}

        else:
            acne_percentages = {"ไม่ได้อัปโหลดรูปภาพ": 100.0}
            
       
        session['acne_results'] = acne_percentages
        session['edge_scores'] = edge_scores

        return render_template("form.html", sex=sex, age=age)
        
    return render_template("form.html")

@app.route("/result", methods=["GET", "POST"])
def result():
    sex = session.get("sex") 
    acne_results = session.get('acne_results', {})
    edge_scores = session.get('edge_scores', {"eat": 0, "hor": 0, "lif": 0, "cle": 0})

    per_hor = per_cle = per_lif = per_eat = 0

    try:
        if request.method == "POST":
            score_gender_specific = 0
            if sex == "1":
                score_gender_specific = int(request.form.get("choice0", 0)) 
            elif sex == "2":
                score_gender_specific = int(request.form.get("choice3", 0))

            score_age = session.get("age", 0.0)
            score_pillow = float(request.form.get("choice4", 0))      
            score_cleansing = int(request.form.get("choice5", 0))   
            score_sleep = float(request.form.get("choice6", 0))      
            score_touch = int(request.form.get("choice7", 0))       
            score_sweet = int(request.form.get("choice8", 0))       
            score_greasy = int(request.form.get("choice9", 0))

           
            score_all = (score_age + score_gender_specific + 
                        score_pillow + score_cleansing + 
                        score_sleep + score_touch + 
                        score_sweet + score_greasy + 
                        edge_scores["eat"] + edge_scores["hor"] + 
                        edge_scores["lif"] + edge_scores["cle"])

            
            if score_all > 0:
                per_all = score_all / 100
                sco_hor = score_age + score_gender_specific + edge_scores["hor"]
                per_hor = round((sco_hor / per_all), 2)

                sco_cle = score_pillow + score_cleansing + edge_scores["cle"]
                per_cle = round((sco_cle / per_all), 2)

                sco_lif = score_sleep + score_touch + edge_scores["lif"]
                per_lif = round((sco_lif / per_all), 2)

                sco_eat = score_sweet + score_greasy + edge_scores["eat"]
                per_eat = round((sco_eat / per_all), 2)

                
                session['per_hor'] = per_hor
                session['per_cle'] = per_cle
                session['per_lif'] = per_lif
                session['per_eat'] = per_eat
        else:
            
            per_hor = session.get('per_hor', 0)
            per_cle = session.get('per_cle', 0)
            per_lif = session.get('per_lif', 0)
            per_eat = session.get('per_eat', 0)

    except Exception as e:
        print(f"Error in calculation: {e}")   

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
    app.run(debug=True, host="0.0.0.0", port=8000)