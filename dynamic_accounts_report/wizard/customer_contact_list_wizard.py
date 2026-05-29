from odoo import models, fields
import io
import xlsxwriter
import base64


class CustomerContactListWizard(models.TransientModel):
    _name = 'customer.contact.list.wizard'
    _description = 'Customer Contact List Report'

    customer_ids = fields.Many2many(
        'res.partner',
        string='Customers',
        domain=[('customer_rank', '>', 0)]
    )

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        # ================= SHEET ================= #

        sheet = workbook.add_worksheet(
            'Customer Contact List'
        )

        # ================= FORMATS ================= #

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
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
            'align': 'left',
            'text_wrap': True
        })

        center_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'align': 'center'
        })

        # ================= COLUMN WIDTH ================= #

        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 22)
        sheet.set_column('C:C', 35)
        sheet.set_column('D:D', 25)
        sheet.set_column('E:E', 45)
        sheet.set_column('F:F', 45)

        # ================= TITLE ================= #

        sheet.merge_range(
            'A1:F2',
            'Customer Contact list',
            title_format
        )

        # ================= HEADERS ================= #

        headers = [
            'Customer full name',
            'Phone numbers',
            'Email',
            'Full name',
            'Bill address',
            'Ship address'
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

        # ================= DATA ================= #

        row += 1

        domain = [
            ('customer_rank', '>', 0)
        ]

        if self.customer_ids:
            domain.append((
                'id',
                'in',
                self.customer_ids.ids
            ))

        customers = self.env[
            'res.partner'
        ].search(domain)

        for rec in customers:

            bill_address = ''

            if rec.contact_address:
                bill_address = rec.contact_address

            shipping_partner = self.env[
                'res.partner'
            ].search([
                ('parent_id', '=', rec.id),
                ('type', '=', 'delivery')
            ], limit=1)

            shipping_address = ''

            if shipping_partner:
                shipping_address = (
                    shipping_partner.contact_address
                )

            phone_numbers = ''

            if rec.phone and rec.mobile:
                phone_numbers = (
                    '%s / %s' % (
                        rec.phone,
                        rec.mobile
                    )
                )

            elif rec.phone:
                phone_numbers = rec.phone

            elif rec.mobile:
                phone_numbers = rec.mobile

            sheet.write(
                row, 0,
                rec.name or '',
                text_format
            )

            sheet.write(
                row, 1,
                phone_numbers,
                center_format
            )

            sheet.write(
                row, 2,
                rec.email or '',
                text_format
            )

            sheet.write(
                row, 3,
                rec.name or '',
                text_format
            )

            sheet.write(
                row, 4,
                bill_address or '',
                text_format
            )

            sheet.write(
                row, 5,
                shipping_address or '',
                text_format
            )

            row += 1

        # ================= CLOSE ================= #

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(
            output.read()
        )

        output.close()

        attachment = self.env[
            'ir.attachment'
        ].create({
            'name': 'Customer_Contact_List.xlsx',
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