from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Sum
from .models import Workout, Meal, Food
from .forms import WorkoutForm, MealForm
from .services import workouts_summary ,meals_summary
import json


# ============================
# WORKOUT
# ============================
@login_required
def workouts_list(request):
    q = request.GET.get("q", "")
    qs = Workout.objects.filter(user=request.user).order_by("-date", "-id")
    if q:
        qs = qs.filter(type__icontains=q)
    paginator = Paginator(qs, 20)
    page = request.GET.get("page")
    items = paginator.get_page(page)
    totals = qs.aggregate(
        total_min=Sum("duration_min"),
        total_kcal=Sum("calories_out"),
        total_steps=Sum("steps"),
    )
    return render(
        request,
        "tracker/workouts_list.html",
        {"items": items, "q": q, "totals": totals},
    )


@login_required
def workouts_create(request):
    if request.method == "POST":
        form = WorkoutForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            return redirect("tracker:workouts_list")
    else:
        form = WorkoutForm()
    return render(request, "tracker/workouts_form.html", {"form": form})


@login_required
def workouts_edit(request, pk):
    obj = get_object_or_404(Workout, pk=pk, user=request.user)
    if request.method == "POST":
        form = WorkoutForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect("tracker:workouts_list")
    else:
        form = WorkoutForm(instance=obj)
    return render(request, "tracker/workouts_form.html", {"form": form, "obj": obj})


@login_required
def workouts_delete(request, pk):
    obj = get_object_or_404(Workout, pk=pk, user=request.user)
    if request.method == "POST":
        obj.delete()
        return redirect("tracker:workouts_list")
    return render(request, "confirm_delete.html", {"obj": obj})


# ============================
# MEAL (AUTO CALO)
# ============================
@login_required
def meals_list(request):
    q = request.GET.get("q", "")
    qs = Meal.objects.filter(user=request.user).order_by("-date", "-id")
    if q:
        # food bây giờ là ForeignKey -> filter theo tên món
        qs = qs.filter(food__name__icontains=q)

    paginator = Paginator(qs, 20)
    page = request.GET.get("page")
    items = paginator.get_page(page)
    totals = qs.aggregate(total_kcal=Sum("calories_in"))

    return render(
        request,
        "tracker/meals_list.html",
        {"items": items, "q": q, "totals": totals},
    )


def _food_kcal_json():
    """
    Trả về dict {id: kcal/100g} để JS dùng tính trước trên form.
    """
    data = {str(f.id): float(f.calories_per_100g or 0) for f in Food.objects.all()}
    return json.dumps(data, ensure_ascii=False)


@login_required
def meals_create(request):
    if request.method == "POST":
        form = MealForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            # calories_in sẽ được tính trong Meal.save()
            obj.save()
            return redirect("tracker:meals_list")
    else:
        form = MealForm()
    ctx = {
        "form": form,
        "food_kcal_json": _food_kcal_json(),
    }
    return render(request, "tracker/meals_form.html", ctx)


@login_required
def meals_edit(request, pk):
    obj = get_object_or_404(Meal, pk=pk, user=request.user)
    if request.method == "POST":
        form = MealForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()  # Meal.save() tự update calories_in
            return redirect("tracker:meals_list")
    else:
        form = MealForm(instance=obj)

    ctx = {
        "form": form,
        "obj": obj,
        "food_kcal_json": _food_kcal_json(),
    }
    return render(request, "tracker/meals_form.html", ctx)


@login_required
def meals_delete(request, pk):
    obj = get_object_or_404(Meal, pk=pk, user=request.user)
    if request.method == "POST":
        obj.delete()
        return redirect("tracker:meals_list")
    return render(request, "confirm_delete.html", {"obj": obj})

@login_required
def workouts_list(request):
    items = Workout.objects.filter(user=request.user).order_by("-date")
    summary = workouts_summary(request.user)

    return render(
        request,
        "tracker/workouts_list.html",
        {
            "items": items,
            "summary": summary,
        }
    )


# ============ LIST MEAL ============
@login_required
def meals_list(request):
    items = Meal.objects.filter(user=request.user).order_by("-date")
    summary = meals_summary(request.user)

    return render(
        request,
        "tracker/meals_list.html",
        {
            "items": items,
            "summary": summary,
        }
    )