from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .models import Session
from django.views import generic
import csv
import json
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.urls import reverse
import pytz
# Create your views here.


class IndexView(generic.ListView):
    template_name = 'readings/index.html'
    model = Session
    paginate_by = 10

    def get_queryset(self):
        return self.model.objects.order_by('-creation_date')

class DetailView(generic.DetailView):
    model = Session
    template_name = 'readings/detail.html'

def download(request, pk):
    session = Session.objects.get(pk=pk)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="' + session.name + '.csv"'

    writer = csv.writer(response)
    writer.writerow(['Gas High','Gas Average','Latitude','Longitude','Date and Time'])
    for measurement in session.measurement_set.all():
        writer.writerow([measurement.gas_high, measurement.gas_avg, measurement.latitude, measurement.longitude, measurement.get_formated_date_time()])
    return response

def post(request):
    if request.method=='POST':
        received_data=json.loads(request.body)
        session_id = int(received_data['session_id'])

        if Session.objects.filter(session_id=session_id):
            session = Session.objects.get(session_id=session_id)
        else:
            session = Session(session_id=session_id)
            session.save()

        measurement = session.measurement_set.create(
            gas_high=int(received_data['gas_high']),
            gas_avg=int(received_data['gas_avg'])
        )
        if received_data['latitude'] != '999999999':
            measurement.latitude=float(received_data['latitude'])
            measurement.longitude=float(received_data['longitude'])
            measurement.date_time = parse_datetime(received_data['date_time']).replace(tzinfo=pytz.UTC)
            measurement.save()
        return HttpResponseRedirect(reverse('index'))
    elif request.method=='GET':
        return HttpResponse("This is only for posting data")
