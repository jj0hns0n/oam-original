from openaerialmap.view import models
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, HttpResponseRedirect 
from django import newforms as forms
from django.conf import settings
from openaerialmap.recaptcha import captcha

import os
import simplejson

# Create your views here.

def attribution_info(request):
    scale = float(request.GET.get("scale", 0))
    bounds = request.GET.get("bbox", "-180,-90,180,90")
    bounds = map(float, bounds.split(","))
    datasources = {}
    datarecords = models.DataRecord.objects.overlaps(bounds).filter(min_scale__lt=scale).filter(max_scale__gt=scale)  
    for record in datarecords:
        datasources[record.datasource.id] = record.datasource
    
    response = render_to_response("attribution.tmpl", {'datasources':datasources})
    if (request.GET.has_key("callback")):
        data = {'attribution':response.content}
        response.content = "%s(%s);" % (request.GET['callback'], simplejson.dumps(data))
    return response    

def agent_create(request, id = None):
    recaptcha_failure = False
    if id:
        form_object = get_object_or_404(models.Agent, pk=id)
        AgentForm = forms.form_for_instance(form_object)
    else:    
        AgentForm = forms.form_for_model(models.Agent)
    
    if request.POST:
        check_captcha = captcha.submit( request.POST['recaptcha_challenge_field'], 
 	                                request.POST['recaptcha_response_field'], 
 	                                settings.RECAPTCHA_PRIVATE_KEY, 
 	                                request.META['REMOTE_ADDR']) 
        f = AgentForm(request.POST)
 	if check_captcha.is_valid:
            if f.is_valid():
                datasource = f.save()
                return HttpResponseRedirect("/")
        else:
 	    recaptcha_failure = True
    else: 
        f = AgentForm()
    return render_to_response("create_form.tmpl", {'form': f, 'type':'Agent', 'recaptcha_failure':recaptcha_failure})

def datasource_create(request, id = None):
    recaptcha_failure = False
    if id:
        form_object = get_object_or_404(models.DataSource, pk=id)
        DataSourceForm = forms.form_for_instance(form_object)
    else:    
        DataSourceForm = forms.form_for_model(models.DataSource)
    DataSourceForm.base_fields['url'].required = False    
    if request.POST:
        check_captcha = captcha.submit( request.POST['recaptcha_challenge_field'],  
 	                                request.POST['recaptcha_response_field'],  
 	                                settings.RECAPTCHA_PRIVATE_KEY,  
 	                                request.META['REMOTE_ADDR']) 
        if check_captcha.is_valid: 
            f = DataSourceForm(request.POST)
            if f.is_valid():
                datasource = f.save()
                return HttpResponseRedirect("/datasource/%s/" % datasource.id)
        else:
            recaptcha_failure = True
    else: 
        f = DataSourceForm()
    return render_to_response("create_form.tmpl", {'form': f, 'type':'DataSource',  'recaptcha_failure':recaptcha_failure})

def datarecord_create(request, id = None):
    recaptcha_failure = False
    if id:
        form_object = get_object_or_404(models.DataRecord, pk=id)
        DataRecordForm = forms.form_for_instance(form_object)
    else:    
        DataRecordForm = forms.form_for_model(models.DataRecord)
    
    if request.POST:
        check_captcha = captcha.submit( request.POST['recaptcha_challenge_field'],         
                                        request.POST['recaptcha_response_field'],
                                        settings.RECAPTCHA_PRIVATE_KEY,
                                        request.META['REMOTE_ADDR'])
        if check_captcha.is_valid:
            f = DataRecordForm(request.POST)
            if f.is_valid():
                datarecord = f.save()
                return HttpResponseRedirect("/datasource/%s/" % datarecord.datasource.id)
        else:
            recaptcha_failure = True
    else: 
        f = DataRecordForm()
    return render_to_response("create_form.tmpl", {'form': f, 'type':'DataRecord', 'recaptcha_failure':recaptcha_failure})

class UploadForm(forms.Form):
    file = forms.FileField()
    id   = forms.IntegerField(required=True,widget=forms.HiddenInput())

def home(request = None):
    datasources = models.DataSource.objects.all().order_by("-id")[:10]
    for datasource in datasources:
        datasource.records = models.DataRecord.objects.filter(datasource=datasource)
    return render_to_response("home.tmpl", {'datasources': datasources}) 
    
def datasource_info(request = None, id = 0):
    if not id:
        datasources = models.DataSource.objects.all().order_by("-id")
        for datasource in datasources:
            datasource.records = models.DataRecord.objects.filter(datasource=datasource)
        return render_to_response("datasource_list.tmpl", {'datasources': datasources}) 
    
    datasource = get_object_or_404(models.DataSource, pk=int(id))
    records = models.DataRecord.objects.filter(datasource=datasource)
    try:
        files = os.listdir("/optistor/viz/openaerialmap/datasources/%s" % datasource.id)
    except OSError:
        files = []
    if request.POST:
        f = UploadForm(request.POST, request.FILES)
        if f.is_valid():
            try:
                os.makedirs("/optistor/viz/openaerialmap/datasources/%s" % request.POST['id'])
            except OSError, E:
                # Directory exists
                pass
            path = "/optistor/viz/openaerialmap/datasources/%s/%s" % (request.POST['id'], request.FILES['file']['filename'])
            f = open(path, "wb")
            f.write(request.FILES['file']['content'])
            return HttpResponse("Uploaded %s." % path)
    else: 
        f = UploadForm(initial= {'id': datasource.id} )
    return render_to_response("datasource_view.tmpl", {'datasource':datasource, 'records': records, 'form': f, 'files': files})

def generate_mapfile(request = None):
    datarecords = models.DataRecord.objects.filter(active=True).order_by("-data_resolution")
    layers = []
    for record in datarecords:
        template = record.type.template
        t = get_template(os.path.join('mapfile', template))
        scales = {'min': int(record.min_scale), 'max': int(record.max_scale)}
        
        description = record.datasource.description
        record.datasource.description = description.replace("\r", "").replace("\n", "").replace('"',"'")         
        c = Context({'obj': record, 'scales': scales})
        layers.append(t.render(c))
    response = render_to_response(os.path.join('mapfile', 'container.tmpl'), {'layers': layers}) 
    response['Content-Type'] = 'text/plain'
    return response


