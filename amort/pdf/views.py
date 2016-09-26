import json
import os
import sys
import tempfile
import logging
import pathlib

from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.generic.base import View

try:
    import convert
except ImportError:
    print('Importing the convert module failed', file=sys.stderr)
    raise

WORKBOOK_PATH = str(pathlib.Path('../amort.ods').absolute())


def ajax_error(message, status=400):
    return HttpResponse(json.dumps({'message': message}), content_type='text/json', status=status)


class AmortPdfView(View):

    def get(self, request):
        name = request.GET['name']
        price = request.GET['price']
        term = request.GET['term']
        rate = request.GET['rate']

        down_percent = request.GET.get('down_percent')
        down = request.GET.get('down')

        if down_percent and down:
            return ajax_error("Pass either a percent or total down")
        if not down_percent and not down:
            return ajax_error('You should specify --down or --down-percent, assuming 20%')

        f, dest = tempfile.mkstemp(suffix='.pdf', prefix='amortXXXXXXXXXX')
        os.close(f)
        try:
            convert.to_pdf(WORKBOOK_PATH, name, price, term, rate, down, down_percent, dest)
            with open(dest, 'rb') as f:
                response = HttpResponse(f, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename=amort.pdf'
                return response
        except Exception as e:
            logging.exception('Error during conversion')
            return ajax_error('Error during conversion', status=500)
        finally:
            os.remove(dest)
