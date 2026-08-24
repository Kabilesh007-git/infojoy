from flask import Flask,render_template,request


app=Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")
    message="welcome to the page"

@app.route("/downdload" , methods=["POST"])
def downdload():
    data=request.form["movie"]

    if len(data)==0:
        return "<h1>enter the name</h1> "

    with open("moviename.txt","w")as txt:
        txt.write(data)

    return render_template("index1.html")



if __name__=="__main__":
    app.run(debug=True,port=5000)