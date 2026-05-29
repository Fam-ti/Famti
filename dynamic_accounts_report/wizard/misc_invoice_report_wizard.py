from odoo import models, fields
import io
import xlsxwriter
import base64


class MiscInvoiceReportWizard(models.TransientModel):
    _name = 'misc.invoice.report.wizard'
    _description = 'Misc Invoice Report Wizard'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    partner_ids = fields.Many2many(
        'res.partner',
        string='Companies'
    )

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        sheet = workbook.add_worksheet(
            'Misc Invoices'
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
        sheet.set_column('B:B', 18)
        sheet.set_column('C:C', 18)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 28)
        sheet.set_column('F:F', 25)
        sheet.set_column('G:G', 28)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 18)
        sheet.set_column('K:K', 15)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 25)
        sheet.set_column('N:N', 30)

        sheet.merge_range(
            'A1:N2',
            'Misc Invoices Report',
            title_format
        )

        headers = [
            'Invoice no',
            'Invoice date',
            'Due date',
            'Container Number',
            'Purchasing company',
            'Purchase order number',
            'Company name',
            'Amount',
            'HST',
            'Total Amount',
            'Currency',
            'Status',
            'Remarks',
            'Comment'
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

        total_amount = 0.0

        for inv in invoices:

            status = 'Paid'

            if inv.payment_state == 'not_paid':
                status = 'Unpaid'
            elif inv.payment_state == 'partial':
                status = 'Partial'

            sheet.write(
                row, 0,
                inv.name or '',
                text_format
            )

            sheet.write(
                row, 1,
                str(inv.invoice_date or ''),
                center_format
            )

            sheet.write(
                row, 2,
                str(inv.invoice_date_due or ''),
                center_format
            )

            sheet.write(
                row, 3,
                inv.ref or '',
                text_format
            )

            sheet.write(
                row, 4,
                inv.company_id.name or '',
                text_format
            )

            sheet.write(
                row, 5,
                inv.invoice_origin or '',
                text_format
            )

            sheet.write(
                row, 6,
                inv.partner_id.name or '',
                text_format
            )

            sheet.write(
                row, 7,
                inv.amount_untaxed or 0.0,
                amount_format
            )

            sheet.write(
                row, 8,
                inv.amount_tax or 0.0,
                amount_format
            )

            sheet.write(
                row, 9,
                inv.amount_total or 0.0,
                amount_format
            )

            sheet.write(
                row, 10,
                inv.currency_id.name or '',
                center_format
            )

            sheet.write(
                row, 11,
                status,
                center_format
            )

            sheet.write(
                row, 12,
                inv.narration or '',
                text_format
            )

            sheet.write(
                row, 13,
                '',
                text_format
            )

            total_amount += (
                inv.amount_total or 0.0
            )

            row += 1

        sheet.merge_range(
            row,
            0,
            row,
            8,
            'TOTAL',
            header_format
        )

        sheet.write(
            row,
            9,
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
            'name': 'Misc_Invoice_Report.xlsx',
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