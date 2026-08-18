from flask import Flask,render_template,request


app=Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/downdload" , methods=["POST"])
def downdload():
    data=request.form["movie"]
    return data


if __name__=="__main__":
    app.run(debug=True,port=5000)