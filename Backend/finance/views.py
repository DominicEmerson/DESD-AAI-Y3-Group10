from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, JsonResponse
from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from django.utils.timezone import localtime
from datetime import datetime
from claims.models import Claim, Accident
import utils
import io
from django.db.models import Q
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def is_finance_team(user):
    """
    Checks if the user is a member of the finance team.
    """
    return user.role == 'finance'

# Finance page
@never_cache 
@login_required
@user_passes_test(is_finance_team)
def finance_page(request):
    """
    Renders the finance dashboard page with filter options and initial claims.
    """
    claims = Claim.objects.all().select_related('accident')
    return render(request, 'finance/finance.html', {'claims': claims})

@login_required
@user_passes_test(is_finance_team)
def filter_claims(request):
    """
    Handles the filtering of claims based on user input and returns JSON data.
    """
    try:
        whiplash = request.GET.get('whiplash', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        min_settlement = request.GET.get('min_settlement', '')
        max_settlement = request.GET.get('max_settlement', '')
        claim_id = request.GET.get('claim_id', '')

        # Start with all claims and select related fields
        claims = Claim.objects.all().select_related('accident')
        
        # Filter by claim ID if provided
        if claim_id:
            claims = claims.filter(id=int(claim_id))
        
        # Filter by whiplash - we need to filter accidents that have injuries with whiplash
        if whiplash:
            claims = claims.filter(
                accident__injury__whiplash=(whiplash == 'Yes')
            ).distinct()
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            claims = claims.filter(accident__accident_date__gte=start_date)
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            claims = claims.filter(accident__accident_date__lte=end_date)
        
        if min_settlement:
            claims = claims.filter(settlement_value__gte=float(min_settlement))
        
        if max_settlement:
            claims = claims.filter(settlement_value__lte=float(max_settlement))

        # Prepare the data for JSON response
        claims_data = []
        for claim in claims:
            # Get the first injury associated with the accident (if any)
            injury = claim.accident.injury_set.first() if claim.accident else None
            
            claims_data.append({
                'id': claim.id,
                'accident_date': claim.accident.accident_date.strftime('%Y-%m-%d') if claim.accident else None,
                'settlement_value': float(claim.settlement_value),
                'whiplash': bool(injury and injury.whiplash),
                'special_health_expenses': float(claim.special_health_expenses),
                'special_reduction': float(claim.special_reduction)
            })

        return JsonResponse({'claims': claims_data})
    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

@login_required
@user_passes_test(is_finance_team)
def generate_report(request):
    """
    Generates a financial report for selected claims.
    """
    claim_ids = request.GET.get('claim_ids', '').split(',')
    include_special_expenses = request.GET.get('include_special_expenses', '') == 'on'
    include_whiplash = request.GET.get('include_whiplash', '') == 'on'

    claims = Claim.objects.filter(id__in=claim_ids)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="financial_report.pdf"'
    
    # Use A4 landscape orientation with minimal margins
    doc = SimpleDocTemplate(response, pagesize=landscape(A4), 
                          rightMargin=10, leftMargin=10, 
                          topMargin=10, bottomMargin=10)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=10
    )
    elements.append(Paragraph('Financial Report', title_style))
    
    # Summary
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=5
    )
    elements.append(Paragraph(f'Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', summary_style))
    elements.append(Paragraph(f'Total Claims: {len(claims)}', summary_style))
    elements.append(Paragraph(f'Total Settlement Value: £{sum(claim.settlement_value for claim in claims):,.2f}', summary_style))
    
    if include_special_expenses:
        total_health_expenses = sum(claim.special_health_expenses for claim in claims)
        total_reduction = sum(claim.special_reduction for claim in claims)
        elements.append(Paragraph(f'Total Special Health Expenses: £{total_health_expenses:,.2f}', summary_style))
        elements.append(Paragraph(f'Total Special Reduction: £{total_reduction:,.2f}', summary_style))
        elements.append(Paragraph(f'Net Total: £{sum(claim.settlement_value for claim in claims) + total_health_expenses - total_reduction:,.2f}', summary_style))
    
    if include_whiplash:
        whiplash_claims = claims.filter(accident__injury__whiplash=True)
        elements.append(Paragraph(f'Claims with Whiplash: {len(whiplash_claims)}', summary_style))
        elements.append(Paragraph(f'Whiplash Settlement Value: £{sum(claim.settlement_value for claim in whiplash_claims):,.2f}', summary_style))
    
    elements.append(Spacer(1, 5))
    
    # Claims Table
    data = [['Claim ID', 'Date', 'Accident Type', 'Whiplash', 'Settlement Value']]
    
    if include_special_expenses:
        data[0].extend(['Health Expenses', 'Reduction', 'Net Value'])
    
    # Simplified table generation without grouping
    for claim in claims:
        row = [
            str(claim.id),
            claim.accident.accident_date.strftime('%Y-%m-%d'),
            claim.accident.accident_type,
            'Yes' if claim.accident.injury_set.filter(whiplash=True).exists() else 'No',
            f'£{claim.settlement_value:,.2f}'
        ]
        if include_special_expenses:
            row.extend([
                f'£{claim.special_health_expenses:,.2f}',
                f'£{claim.special_reduction:,.2f}',
                f'£{claim.settlement_value + claim.special_health_expenses - claim.special_reduction:,.2f}'
            ])
        data.append(row)
    
    # Calculate column widths based on A4 landscape dimensions
    page_width = landscape(A4)[0] - 20  # Subtract margins
    if include_special_expenses:
        col_widths = [page_width * 0.08, page_width * 0.12, page_width * 0.2, page_width * 0.08, 
                     page_width * 0.12, page_width * 0.12, page_width * 0.12, page_width * 0.12]
    else:
        col_widths = [page_width * 0.12, page_width * 0.12, page_width * 0.3, page_width * 0.08, 
                     page_width * 0.38]
    
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    return response

@login_required
@user_passes_test(is_finance_team)
def generate_invoice(request):
    """
    Generates an invoice for selected claims.
    """
    claim_ids = request.GET.get('claim_ids', '').split(',')
    invoice_number = request.GET.get('invoice_number', '')
    client_reference = request.GET.get('client_reference', '')
    include_breakdown = request.GET.get('include_expense_breakdown', '') == 'on'

    claims = Claim.objects.filter(id__in=claim_ids)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_number}.pdf"'
    
    # Use A4 landscape orientation with minimal margins
    doc = SimpleDocTemplate(response, pagesize=landscape(A4), 
                          rightMargin=10, leftMargin=10, 
                          topMargin=10, bottomMargin=10)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=10
    )
    elements.append(Paragraph('Invoice', title_style))
    
    # Invoice Details
    details_style = ParagraphStyle(
        'Details',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=5
    )
    elements.append(Paragraph(f'Invoice Number: {invoice_number}', details_style))
    if client_reference:
        elements.append(Paragraph(f'Client Reference: {client_reference}', details_style))
    elements.append(Paragraph(f'Date: {datetime.now().strftime("%Y-%m-%d")}', details_style))
    
    elements.append(Spacer(1, 5))
    
    # Claims Table
    data = [['Claim ID', 'Date', 'Accident Type', 'Settlement Value']]
    
    if include_breakdown:
        data[0].extend(['Health Expenses', 'Reduction', 'Net Value'])
    
    for claim in claims:
        row = [
            str(claim.id),
            claim.accident.accident_date.strftime('%Y-%m-%d'),
            claim.accident.accident_type,
            f'£{claim.settlement_value:,.2f}'
        ]
        if include_breakdown:
            row.extend([
                f'£{claim.special_health_expenses:,.2f}',
                f'£{claim.special_reduction:,.2f}',
                f'£{claim.settlement_value + claim.special_health_expenses - claim.special_reduction:,.2f}'
            ])
        data.append(row)
    
    # Calculate column widths based on A4 landscape dimensions
    page_width = landscape(A4)[0] - 20  # Subtract margins
    if include_breakdown:
        col_widths = [
            page_width * 0.08,  # Claim ID
            page_width * 0.12,  # Date
            page_width * 0.20,  # Accident Type
            page_width * 0.12,  # Settlement Value
            page_width * 0.12,  # Health Expenses
            page_width * 0.12,  # Reduction
            page_width * 0.12   # Net Value
        ]
    else:
        col_widths = [
            page_width * 0.08,  # Claim ID
            page_width * 0.12,  # Date
            page_width * 0.50,  # Accident Type
            page_width * 0.30   # Settlement Value
        ]
    
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    return response 