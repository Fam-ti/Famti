from odoo import models, fields
import io
import xlsxwriter
import base64


class PurchaseOrderReportWizard(models.TransientModel):
    _name = 'purchase.order.report.wizard'
    _description = 'Purchase Order Report Wizard'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    partner_ids = fields.Many2many(
        'res.partner',
        string='Vendors'
    )

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        sheet = workbook.add_worksheet(
            'Purchase Order'
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
            'num_format': '#,##0.00',
            'align': 'right'
        })

        sheet.set_column('A:A', 18)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:D', 40)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 18)
        sheet.set_column('H:H', 35)
        sheet.set_column('I:I', 25)
        sheet.set_column('J:J', 25)

        sheet.merge_range(
            'A1:J2',
            'FAM PURCHASE ORDER SHEET',
            title_format
        )

        headers = [
            'PO Date',
            'PO number',
            'Vendor/ supplier',
            'Description',
            'Amount',
            'HST',
            'Total Amount',
            'Remarks/ Special Instructions',
            'Payment Terms',
            'Delivery Terms'
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
            ('state', 'in', ['purchase', 'done'])
        ]

        if self.start_date:
            domain.append((
                'date_order',
                '>=',
                self.start_date
            ))

        if self.end_date:
            domain.append((
                'date_order',
                '<=',
                self.end_date
            ))

        if self.partner_ids:
            domain.append((
                'partner_id',
                'in',
                self.partner_ids.ids
            ))

        purchase_orders = self.env[
            'purchase.order'
        ].search(domain)

        row += 1

        total_amount = 0.0

        for po in purchase_orders:

            description = ', '.join(
                po.order_line.mapped(
                    'name'
                )
            )

            sheet.write(
                row, 0,
                str(po.date_order.date())
                if po.date_order else '',
                center_format
            )

            sheet.write(
                row, 1,
                po.name or '',
                text_format
            )

            sheet.write(
                row, 2,
                po.partner_id.name or '',
                text_format
            )

            sheet.write(
                row, 3,
                description or '',
                text_format
            )

            sheet.write(
                row, 4,
                po.amount_untaxed or 0.0,
                amount_format
            )

            sheet.write(
                row, 5,
                po.amount_tax or 0.0,
                amount_format
            )

            sheet.write(
                row, 6,
                po.amount_total or 0.0,
                amount_format
            )

            sheet.write(
                row, 7,
                po.notes or '',
                text_format
            )

            sheet.write(
                row, 8,
                po.payment_term_id.name or '',
                text_format
            )

            sheet.write(
                row, 9,
                po.incoterm_id.name or '',
                text_format
            )

            total_amount += (
                po.amount_total or 0.0
            )

            row += 1

        sheet.merge_range(
            row,
            0,
            row,
            5,
            'TOTAL',
            header_format
        )

        sheet.write(
            row,
            6,
            total_amount,
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
            'name': 'Purchase_Order_Report.xlsx',
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