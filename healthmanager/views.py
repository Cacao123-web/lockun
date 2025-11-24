from django.shortcuts import render
from django.http import HttpRequest

def search(request: HttpRequest):
    q = (request.GET.get("q") or "").strip()
    results = []

    if q:
        kw = q.lower()
        if any(k in kw for k in ["tập", "workout", "gym"]):
            results.append({"title": "Nhật ký tập luyện", "url": "/tracker/workouts/"})
        if any(k in kw for k in ["ăn", "meal", "dinh dưỡng", "calo", "thịt", "rau"]):
            results.append({"title": "Nhật ký dinh dưỡng", "url": "/tracker/meals/"})
        if any(k in kw for k in ["mục tiêu", "goal", "giảm cân", "tăng cơ"]):
            results.append({"title": "Mục tiêu sức khỏe", "url": "/goals/"})
        if any(k in kw for k in ["báo cáo", "report", "thống kê"]):
            results.append({"title": "Báo cáo", "url": "/reports/"})

    context = {"q": q, "results": results}
    return render(request, "search_results.html", context)
