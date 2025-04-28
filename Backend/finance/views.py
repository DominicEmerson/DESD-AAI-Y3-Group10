from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.utils.timezone import localtime
import utils
import io

# Finance page
@never_cache 
@login_required
@user_passes_test(utils.is_finance, login_url='role_redirect')
def finance_page(request):
    return render(request, 'finance/finance.html')

@login_required
def generate_report(request):
    # Create a PDF in memory
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.drawString(100, 750, "This is a placeholder for the report.")
    p.showPage()
    p.save()
    buffer.seek(0)

    # Return the PDF response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="report.pdf"'
    return response

@login_required
def generate_invoice(request):
    # Create a PDF in memory
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    # Add content to the PDF
    p.drawString(100, 750, "Invoice")
    p.drawString(100, 730, "Item: Insurance")
    p.drawString(100, 710, "Description: Testing Invoice")
    p.drawString(100, 690, "Price: £1000.00")
    # Finalise the PDF
    p.showPage()
    p.save()
    buffer.seek(0)

    # Return the PDF response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="invoice.pdf"'
    return response