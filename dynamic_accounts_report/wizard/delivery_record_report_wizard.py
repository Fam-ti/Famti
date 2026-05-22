from odoo import models, fields
import io
import xlsxwriter
import base64


class DeliveryRecordReportWizard(models.TransientModel):
    _name = 'delivery.record.report.wizard'
    _description = 'Delivery Record Customer Report Wizard'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    partner_ids = fields.Many2many(
        'res.partner',
        string='Customers'
    )

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        sheet = workbook.add_worksheet(
            'Delivery Records'
        )

        title_format = workbook.add_format({
            'align': 'center',
            'bold': True,
            'font_size': 16,
            'border': 1
        })

        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#D9D9D9',
            'font_size': 10,
            'text_wrap': True
        })

        text_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'align': 'left'
        })

        center_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'align': 'center'
        })

        amount_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'align': 'right',
            'num_format': '#,##0.00'
        })

        total_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'bg_color': '#D9D9D9',
            'font_size': 10,
            'align': 'center'
        })

        sheet.set_column('A:A', 18)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 25)
        sheet.set_column('I:I', 30)
        sheet.set_column('J:J', 30)

        sheet.merge_range(
            'A1:J2',
            'DELIVERY RECORD OF CUSTOMER SHEET',
            title_format
        )

        headers = [
            'DATE',
            'Company Name',
            'Invoice no',
            'PO #',
            'NO. OF ROLLS',
            'SKIDS',
            'KG/lbs',
            'Location',
            'Transport company',
            'Remarks'
        ]

        row = 3
        col = 0

        for header in headers:
            sheet.write(
                row,
                col,
                header,
                header_format
            )
            col += 1


        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ]

        if self.start_date:
            domain.append((
                'invoice_date',
                '>=',
                self.start_date
            ))

        if self.end_date:
            domain.append((
                'invoice_date',
                '<=',
                self.end_date
            ))

        if self.partner_ids:
            domain.append((
                'partner_id',
                'in',
                self.partner_ids.ids
            ))

        invoices = self.env[
            'account.move'
        ].search(domain)

        row += 1

        total_rolls = 0.0
        total_skids = 0.0
        total_weight = 0.0

        for inv in invoices:

            qty_rolls = sum(
                inv.invoice_line_ids.mapped(
                    'quantity'
                )
            )

            total_weight_invoice = sum(
                inv.invoice_line_ids.mapped(
                    'price_subtotal'
                )
            )

            sheet.write(
                row, 0,
                str(inv.invoice_date or ''),
                center_format
            )

            sheet.write(
                row, 1,
                inv.partner_id.name or '',
                text_format
            )

            sheet.write(
                row, 2,
                inv.name or '',
                text_format
            )

            sheet.write(
                row, 3,
                inv.invoice_origin or '',
                text_format
            )

            sheet.write(
                row, 4,
                qty_rolls,
                center_format
            )

            sheet.write(
                row, 5,
                '',
                center_format
            )

            sheet.write(
                row, 6,
                total_weight_invoice,
                amount_format
            )

            sheet.write(
                row, 7,
                inv.partner_shipping_id.city or '',
                text_format
            )

            sheet.write(
                row, 8,
                '',
                text_format
            )

            sheet.write(
                row, 9,
                inv.narration or '',
                text_format
            )

            total_rolls += qty_rolls
            total_weight += total_weight_invoice

            row += 1

        sheet.merge_range(
            row,
            0,
            row,
            3,
            'TOTAL',
            header_format
        )

        sheet.write(
            row,
            4,
            total_rolls,
            total_format
        )

        sheet.write(
            row,
            5,
            total_skids,
            total_format
        )

        sheet.write(
            row,
            6,
            total_weight,
            total_format
        )

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(
            output.read()
        )

        output.close()

        attachment = self.env[
            'ir.attachment'
        ].create({
            'name': 'Delivery_Record_Report.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype':
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true'
                   % attachment.id,
            'target': 'self',
        }