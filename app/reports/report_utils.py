# from io import BytesIO
# from django.http import HttpResponse
# from django.template.loader import get_template
# from xhtml2pdf import pisa
# from datetime import datetime
# import csv
#
#
# def render_to_pdf(template_src, context_dict={}):
#     """Render HTML template to PDF"""
#     template = get_template(template_src)
#     html = template.render(context_dict)
#     result = BytesIO()
#
#     # Create PDF
#     pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
#
#     if not pdf.err:
#         return result.getvalue()
#     return None
#
#
# def export_to_pdf(template_src, context_dict, filename):
#     """Generate PDF response"""
#     pdf = render_to_pdf(template_src, context_dict)
#
#     if pdf:
#         response = HttpResponse(pdf, content_type='application/pdf')
#         content = f"attachment; filename=\"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf\""
#         response['Content-Disposition'] = content
#         return response
#     return HttpResponse("Error generating PDF", status=500)
#
#
# def export_to_csv(data, filename, field_names):
#     """Generate CSV response"""
#     response = HttpResponse(content_type='text/csv')
#     response[
#         'Content-Disposition'] = f'attachment; filename="{filename}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
#
#     writer = csv.DictWriter(response, fieldnames=field_names)
#     writer.writeheader()
#
#     for row in data:
#         writer.writerow(row)
#
#     return response
#
#
# def get_report_context(form, title, **extra_context):
#     """Prepare common context for reports"""
#     start_date, end_date = form.get_date_range()
#
#     context = {
#         'title': title,
#         'start_date': start_date,
#         'end_date': end_date,
#         'report_type': form.cleaned_data.get('report_type'),
#         'form': form,
#         'generated_at': datetime.now(),
#     }
#
#     # Add any extra context
#     context.update(extra_context)
#     return context
