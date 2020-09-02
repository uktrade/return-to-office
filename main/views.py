from django.shortcuts import render

def index(req):
    ctx = {}
    ctx["name"] = req.user.first_name

    return render(req, "main/hello.html", ctx)
