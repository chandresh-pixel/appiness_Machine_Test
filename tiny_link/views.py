# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.template import RequestContext
from django.db.models import F
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from tiny_link import models
import datetime
import functools

def home(request):
    url_error = False
    url_input = ""
    shortened_url = ""
    
    if request.method == "POST":
        validator = URLValidator()
        try:
            url_input = request.POST.get("url", None)
            if not url_input:
                url_error = True
            else:
                validator(url_input)
        except ValidationError:
            url_error = True

        if not url_error:
            link_db = models.Link()
            link_db.link = url_input
            shortened_url = request.build_absolute_uri(link_db.get_short_id())
            link_db.short_link = shortened_url
            link_db.save()
            url_input = ""
            #shortened_url = "%s/%s"%(request.META["HTTP_HOST"], link_db.get_short_id())

    return render(request, "index.html",
            {"error":url_error, "url":url_input, "shorturl":shortened_url})

def link(request, id):
    print(id)
    db_id = models.Link.decode_id(id)
    print(db_id)
    link_db = get_object_or_404(models.Link, id=db_id)
    print("Link:",link_db.link)

    models.Link.objects.filter(id=db_id).update(hits=F('hits')+1) # Update the link hits

    if not models.HitsDatePoint.objects.filter(link=link_db, day=datetime.date.today()).exists():
        x = models.HitsDatePoint()
        x.day = datetime.date.today()
        x.link = link_db
        try:
            x.save()
        except Exception as e:
            print("Possible corruption: %s"%e)

    models.HitsDatePoint.objects.filter(day=datetime.date.today(), link=link_db).update(hits=F('hits')+1)

    return redirect(link_db.link)

def stats(request, id):
    db_id = models.Link.decode_id(id)
    link_db = get_object_or_404(models.Link, id=db_id)

    stats = models.HitsDatePoint.objects.filter(day__gt=datetime.date.today()-datetime.timedelta(days=30),
                                                link=link_db).all()

    link_url = request.build_absolute_uri("/"+link_db.get_short_id()) # make it an absolute one

    return render(request, "stats.html", {"stats":stats, "link":link_db, "link_url":link_url}
                                        )

def allLinks(request):
    # db_id = models.Link.decode_id(id)
    # link_db = get_object_or_404(models.Link)
    return render(request, "allLinks.html",{"links":models.Link.objects.all()})
