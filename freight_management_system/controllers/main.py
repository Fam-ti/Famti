import io
import base64

from odoo import http
from odoo.http import request

import xlsxwriter


class FreightXlsxController(http.Controller):

    @http.route(
        '/freight/container_tracking_xlsx/<int:order_id>',
        type='http',
        auth='user'
    )
    def download_container_tracking_xlsx(self, order_id, **kwargs):

        order = request.env['freight.order'].sudo().browse(order_id)

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Container Tracking')

        # =====================================================
        # FORMATS
        # =====================================================

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1,
            'align': 'center',
        })

        text_format = workbook.add_format({
            'border': 1,
        })

        date_format = workbook.add_format({
            'border': 1,
            'num_format': 'dd-mm-yyyy',
        })

        # =====================================================
        # HEADERS
        # =====================================================

        headers = [
            'PO DATE',
            'PO No.',
            'Pi No.',
            'Pi date',
            'ETD',
            'ORIGIN',
            'CUSTOMER',
            'shipping line',
            'Container No',
        ]

        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)

        # =====================================================
        # DATA
        # =====================================================

        row = 1

        for track in order.tracking_ids:

            if track.po_date:
                sheet.write_datetime(
                    row, 0,
                    track.po_date,
                    date_format
                )
            else:
                sheet.write(row, 0, '', text_format)

            sheet.write(row, 1, track.po_no or '', text_format)

            sheet.write(row, 2, track.pi_no or '', text_format)

            if track.pi_date:
                sheet.write_datetime(
                    row, 3,
                    track.pi_date,
                    date_format
                )
            else:
                sheet.write(row, 3, '', text_format)

            if track.etd:
                sheet.write_datetime(
                    row, 4,
                    track.etd,
                    date_format
                )
            else:
                sheet.write(row, 4, '', text_format)

            sheet.write(row, 5, track.origin or '', text_format)

            sheet.write(
                row,
                6,
                track.customer_id.name if track.customer_id else '',
                text_format
            )

            sheet.write(
                row,
                7,
                track.shipping_line or '',
                text_format
            )

            sheet.write(
                row,
                8,
                track.container_no or '',
                text_format
            )

            row += 1

        workbook.close()

        output.seek(0)

        xlsx_data = output.read()

        filename = 'Container_Tracking.xlsx'

        return request.make_response(
            xlsx_data,
            headers=[
                (
                    'Content-Type',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ),
                (
                    'Content-Disposition',
                    f'attachment; filename={filename};'
                )
            ]
        )