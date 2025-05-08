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
    return user.role == 'finance'  # Return True if user is in finance team

# Finance page
@never_cache 
@login_required
@user_passes_test(is_finance_team)
def finance_page(request):
    """
    Renders the finance dashboard page with filter options and initial claims.
    """
    claims = Claim.objects.all().select_related('accident')  # Get all claims with related accidents
    return render(request, 'finance/finance.html', {'claims': claims})  # Render finance dashboard

@login_required
@user_passes_test(is_finance_team)
def filter_claims(request):
    """
    Handles the filtering of claims based on user input and returns JSON data.
    """
    try:
        whiplash = request.GET.get('whiplash', '')  # Get whiplash filter value
        start_date = request.GET.get('start_date', '')  # Get start date filter value
        end_date = request.GET.get('end_date', '')  # Get end date filter value
        min_settlement = request.GET.get('min_settlement', '')  # Get minimum settlement filter value
        max_settlement = request.GET.get('max_settlement', '')  # Get maximum settlement filter value
        claim_id = request.GET.get('claim_id', '')  # Get claim ID filter value

        # Start with all claims and select related fields
        claims = Claim.objects.all().select_related('accident')  # Get all claims with related accidents
        
        # Filter by claim ID if provided
        if claim_id:
            claims = claims.filter(id=int(claim_id))  # Filter claims by ID
        
        # Filter by whiplash - we need to filter accidents that have injuries with whiplash
        if whiplash:
            claims = claims.filter(
                accident__injury__whiplash=(whiplash == 'Yes')  # Filter claims with whiplash
            ).distinct()  # Ensure distinct results
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()  # Parse start date
            claims = claims.filter(accident__accident_date__gte=start_date)  # Filter claims by start date
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()  # Parse end date
            claims = claims.filter(accident__accident_date__lte=end_date)  # Filter claims by end date
        
        if min_settlement:
            claims = claims.filter(settlement_value__gte=float(min_settlement))  # Filter claims by minimum settlement
        
        if max_settlement:
            claims = claims.filter(settlement_value__lte=float(max_settlement))  # Filter claims by maximum settlement

        # Prepare the data for JSON response
        claims_data = []  # Initialise list for claims data
        for claim in claims:
            # Get the first injury associated with the accident (if any)
            injury = claim.accident.injury_set.first() if claim.accident else None  # Get first injury
            
            claims_data.append({
                'id': claim.id,  # Claim ID
                'accident_date': claim.accident.accident_date.strftime('%Y-%m-%d') if claim.accident else None,  # Accident date
                'settlement_value': float(claim.settlement_value),  # Settlement value
                'whiplash': bool(injury and injury.whiplash),  # Whiplash status
                'special_health_expenses': float(claim.special_health_expenses),  # Special health expenses
                'special_reduction': float(claim.special_reduction)  # Special reduction
            })

        return JsonResponse({'claims': claims_data})  # Return claims data as JSON
    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e),  # Return error message
            'traceback': traceback.format_exc()  # Return traceback for debugging
        }, status=500)

@login_required
@user_passes_test(is_finance_team)
def generate_report(request):
    """
    Generates a financial report for selected claims.
    """
    claim_ids = request.GET.get('claim_ids', '').split(',')  # Get claim IDs from request
    include_special_expenses = request.GET.get('include_special_expenses', '') == 'on'  # Check if special expenses should be included
    include_whiplash = request.GET.get('include_whiplash', '') == 'on'  # Check if whiplash claims should be included

    claims = Claim.objects.filter(id__in=claim_ids)  # Get claims based on IDs
    
    response = HttpResponse(content_type='application/pdf')  # Create PDF response
    response['Content-Disposition'] = 'attachment; filename="financial_report.pdf"'  # Set filename for download
    
    # Use A4 landscape orientation with minimal margins
    doc = SimpleDocTemplate(response, pagesize=landscape(A4), 
                          rightMargin=10, leftMargin=10, 
                          topMargin=10, bottomMargin=10)  # Create document template
    elements = []  # Initialise elements for the PDF
    styles = getSampleStyleSheet()  # Get sample styles for PDF
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=10
    )
    elements.append(Paragraph('Financial Report', title_style))  # Add title to PDF
    
    # Summary
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=5
    )
    elements.append(Paragraph(f'Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', summary_style))  # Add report generation date
    elements.append(Paragraph(f'Total Claims: {len(claims)}', summary_style))  # Add total claims count
    elements.append(Paragraph(f'Total Settlement Value: £{sum(claim.settlement_value for claim in claims):,.2f}', summary_style))  # Add total settlement value
    
    if include_special_expenses:
        total_health_expenses = sum(claim.special_health_expenses for claim in claims)  # Calculate total health expenses
        total_reduction = sum(claim.special_reduction for claim in claims)  # Calculate total reductions
        elements.append(Paragraph(f'Total Special Health Expenses: £{total_health_expenses:,.2f}', summary_style))  # Add total health expenses to PDF
        elements.append(Paragraph(f'Total Special Reduction: £{total_reduction:,.2f}', summary_style))  # Add total reductions to PDF
        elements.append(Paragraph(f'Net Total: £{sum(claim.settlement_value for claim in claims) + total_health_expenses - total_reduction:,.2f}', summary_style))  # Add net total to PDF
    
    if include_whiplash:
        whiplash_claims = claims.filter(accident__injury__whiplash=True)  # Get claims with whiplash
        elements.append(Paragraph(f'Claims with Whiplash: {len(whiplash_claims)}', summary_style))  # Add count of whiplash claims to PDF
        elements.append(Paragraph(f'Whiplash Settlement Value: £{sum(claim.settlement_value for claim in whiplash_claims):,.2f}', summary_style))  # Add total settlement value for whiplash claims to PDF
    
    elements.append(Spacer(1, 5))  # Add space before table
    
    # Claims Table
    data = [['Claim ID', 'Date', 'Accident Type', 'Whiplash', 'Settlement Value']]  # Table header
    
    if include_special_expenses:
        data[0].extend(['Health Expenses', 'Reduction', 'Net Value'])  # Add additional columns if special expenses are included
    
    # Simplified table generation without grouping
    for claim in claims:
        row = [
            str(claim.id),  # Claim ID
            claim.accident.accident_date.strftime('%Y-%m-%d'),  # Accident date
            claim.accident.accident_type,  # Accident type
            'Yes' if claim.accident.injury_set.filter(whiplash=True).exists() else 'No',  # Whiplash status
            f'£{claim.settlement_value:,.2f}'  # Settlement value
        ]
        if include_special_expenses:
            row.extend([
                f'£{claim.special_health_expenses:,.2f}',  # Special health expenses
                f'£{claim.special_reduction:,.2f}',  # Special reduction
                f'£{claim.settlement_value + claim.special_health_expenses - claim.special_reduction:,.2f}'  # Net value
            ])
        data.append(row)  # Add row to table data
    
    # Calculate column widths based on A4 landscape dimensions
    page_width = landscape(A4)[0] - 20  # Subtract margins
    if include_special_expenses:
        col_widths = [page_width * 0.08, page_width * 0.12, page_width * 0.2, page_width * 0.12, 
                     page_width * 0.12, page_width * 0.12, page_width * 0.12]  # Column widths for table
    else:
        col_widths = [page_width * 0.12, page_width * 0.12, page_width * 0.3, page_width * 0.08, 
                     page_width * 0.38]  # Column widths for table without special expenses
    
    table = Table(data, colWidths=col_widths, repeatRows=1)  # Create table with data and column widths
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Header background colour
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text colour
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Centre align all cells
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold font for header
        ('FONTSIZE', (0, 0), (-1, 0), 8),  # Font size for header
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),  # Padding for header
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Background colour for body
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),  # Text colour for body
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),  # Font for body
        ('FONTSIZE', (0, 1), (-1, -1), 7),  # Font size for body
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Grid for table
        ('LEFTPADDING', (0, 0), (-1, -1), 2),  # Padding for left side
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),  # Padding for right side
        ('TOPPADDING', (0, 0), (-1, -1), 1),  # Padding for top
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),  # Padding for bottom
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical alignment
        ('WORDWRAP', (0, 0), (-1, -1), True),  # Enable word wrap
    ]))  # Set table style
    
    elements.append(table)  # Add table to elements
    doc.build(elements)  # Build the PDF document
    
    return response  # Return the PDF response