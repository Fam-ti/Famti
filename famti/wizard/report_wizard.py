import io
import base64
import xlsxwriter
from odoo import models, fields

class SaleReportWizard(models.TransientModel):
    _name = 'sale.report.wizard'
    _description = 'Sales Report Wizard'

    date_from = fields.Date()
    date_to = fields.Date()
    partner_id = fields.Many2one('res.partner')

    def action_generate_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Sales Report')

        bold = workbook.add_format({'bold': True})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        number_format = workbook.add_format({'num_format': '#,##0.00'})

        headers = ['Customer', 'Order', 'Date', 'Product', 'Treatment In', 'Treatment Out', 'Thickness', 'Width', 'core_id', 'Length', 'Quantity', 'Total']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)

        domain = [('state', 'in', ['sale', 'done'])]

        if self.date_from:
            domain.append(('date_order', '>=', self.date_from))
        if self.date_to:
            domain.append(('date_order', '<=', self.date_to))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))

        orders = self.env['sale.order'].search(domain, order="date_order asc")

        row = 1
        grand_total = 0

        for order in orders:
            for line in order.order_line:

                sheet.write(row, 0, order.partner_id.name or '')
                sheet.write(row, 1, order.name or '')
                sheet.write(row, 2, order.date_order, date_format)
                sheet.write(row, 3, line.product_template_id.name or '')
                sheet.write(row, 4, line.treatment_in or '')
                sheet.write(row, 5, line.treatment_out or '')
                sheet.write(row, 6, line.thickness_val or 0)
                sheet.write(row, 7, line.width_val or 0)
                sheet.write(row, 8, line.core_id or '')
                sheet.write(row, 9, line.length_val or 0)
                sheet.write(row, 10, line.product_uom_qty or 0)
                sheet.write(row, 11, line.price_subtotal or 0, number_format)

                grand_total += line.price_subtotal or 0
                row += 1

        sheet.write(row, 10, 'Grand Total', bold)
        sheet.write(row, 11, grand_total, number_format)

        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 25)
        sheet.set_column('E:E', 12)
        sheet.set_column('F:F', 15)

        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Sales_Report.xlsx',
            'type': 'binary',
            'datas': file_data,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
    

class DailyInventoryReportWizard(models.TransientModel):
    _name = 'daily.inventory.report.wizard'
    _description = 'Daily Inventory Report Wizard'

    from_date = fields.Date(required=True)
    to_date = fields.Date(required=True)

    def action_print_report(self):

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        sheet = workbook.add_worksheet('Daily Inventory Report')

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
            'bg_color': '#FFFF00',
            'border': 1,
        })

        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'text_wrap': True,
            'bg_color': '#D9D9D9',
        })

        cell_format = workbook.add_format({
            'border': 1,
        })

        number_format = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00',
        })

        date_format = workbook.add_format({
            'border': 1,
            'num_format': 'dd-mm-yyyy',
        })


        title = (
            f'Daily Inventory Report '
            f'({self.from_date} to {self.to_date})'
        )

        sheet.merge_range('A1:AA1', title, title_format)

        headers = [
            'DATE',
            'Film Type',
            'Product',
            'ROLL NUMBER',
            'THICK (µ)',
            'WIDTH (MM)',
            'LENGTH (MTRS)',
            'WEIGHT (KGS)',
            'TREATMENT',
            'SLIT ROLL NUMBER',
            'SLIT WIDTH (MM)',
            'CORE ID (")',
            'LENGTH (MTRS)',
            'CORE WEIGHT (KGS)',
            'GROSS WEIGHT (KGS)',
            'NET WEIGHT (KGS)',
            'THEORITICAL WEIGHT (KGS)',
            'JOINT',
            'TREATMENT',
            'SALES ORDER',
            'BUYER',
            'REMARKS IF ANY',
            'TRIM WIDTH MM',
            'TRIM WEIGHT KG',
            'BALANCE',
            'OFFCUT - MM',
            'OFF CUT-WEIGHT',
        ]

        row = 2

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)


        row += 1

        pickings = self.env['stock.picking'].search([
            ('scheduled_date', '>=', self.from_date),
            ('scheduled_date', '<=', self.to_date),
        ])

        for picking in pickings:

            for line in picking.move_line_ids:

                sale = picking.sale_id

                product = line.product_id

                lot = line.lot_id

                sheet.write_datetime(row, 0, picking.scheduled_date, date_format)
                sheet.write(row, 1,product.categ_id.name or '', cell_format)
                sheet.write(row, 2,product.name or '',cell_format)
                sheet.write(row, 3,lot.name or '',cell_format)
                sheet.write(row, 4,product.thickness_val or '',cell_format)
                sheet.write(row, 5,product.width_val or '',cell_format)
                sheet.write( row, 6,getattr(line, 'length', ''),cell_format)
                sheet.write( row, 7,line.quantity or 0.0,number_format)
                sheet.write( row, 8,getattr(line, 'treatment', ''),cell_format)
                sheet.write( row, 9,getattr(line, 'slit_roll_number', ''),cell_format)
                sheet.write(row, 10,getattr(line, 'slit_width', ''),cell_format)
                sheet.write(row, 11,getattr(line, 'core_id', ''),cell_format)
                sheet.write(row, 12,getattr(line, 'length_mtrs', ''),cell_format)
                sheet.write(row, 13,getattr(line, 'core_weight', ''),number_format)
                sheet.write(row, 14,getattr(line, 'gross_weight', ''),number_format)
                sheet.write(row, 15,getattr(line, 'net_weight', ''), number_format)
                sheet.write(row, 16, getattr(line, 'theoretical_weight', ''), number_format)
                sheet.write( row, 17, getattr(line, 'joint', ''), cell_format)
                sheet.write(row, 18, getattr(line, 'treatment_2', ''),cell_format)
                sheet.write(row, 19, sale.name or '', cell_format)
                sheet.write(row, 20,sale.partner_id.name or '', cell_format)
                sheet.write(row, 21, picking.note or '', cell_format)
                sheet.write(row, 22, getattr(line, 'trim_width', ''), number_format)
                sheet.write(row, 23, getattr(line, 'trim_weight', ''), number_format)
                sheet.write(row, 24, getattr(line, 'balance', ''), number_format)
                sheet.write(row, 25, getattr(line, 'offcut_mm', ''), number_format)
                sheet.write( row, 26, getattr(line, 'offcut_weight', ''),number_format)

                row += 1


        sheet.set_column('A:AA', 18)

        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': 'Daily_Inventory_Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype':
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
    
class MisMonthlyReportWizard(models.TransientModel):
    _name = 'mis.monthly.report.wizard'
    _description = 'MIS Monthly Report Wizard'

    month = fields.Selection([
        ('january', 'January'),
        ('february', 'February'),
        ('march', 'March'),
        ('april', 'April'),
        ('may', 'May'),
        ('june', 'June'),
        ('july', 'July'),
        ('august', 'August'),
        ('september', 'September'),
        ('october', 'October'),
        ('november', 'November'),
        ('december', 'December'),
    ], string="Month")

    year = fields.Char(string="Year")

    machine = fields.Char(string="Machine")

    def action_mis_report_excel(self):

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('MIS Report')

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 18,
            'border': 1,
        })

        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#FFF200',
        })

        table_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })

        bold_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })


        sheet.set_column('A:A', 35)
        sheet.set_column('B:H', 15)
        sheet.merge_range('A1:C1', 'MONTH/YEAR', bold_format)
        sheet.merge_range('D1:H1',
                          f'{self.month.upper() if self.month else ""} {self.year or ""}',
                          title_format)

        sheet.merge_range('A2:C2', 'Machine #', bold_format)
        sheet.merge_range('D2:H2', self.machine or '', bold_format)
        sheet.merge_range('A3:C3', 'Shifts', bold_format)
        sheet.merge_range('D3:H3', 'DAY SHIFT/8 HOURS ONLY PER DAY', bold_format)
        sheet.merge_range('A5:H5', 'MIS SLITTING REPORT', header_format)
        labels = [
            'Slitting Input (Kgs)',
            'Slitting Output (Kgs)',
            'Approved Output (SOLD) (Kgs)',
            'Offcut Qty (Kgs) (Useable/back to stock)',
            'Output Efficiency (%)',
            'Approved Efficiency(%)',
            'Total Waste (kgs)',
            'Waste %',
            'Trim Waste (Kgs)',
            'Trim Waste (%)',
            'Other Waste (kg) (non-usable due to insufficient length or roll damage)',
            'Other Waste (%)',
            'Remarks if any',
        ]

        row = 5

        for label in labels:
            sheet.merge_range(row, 0, row, 2, label, bold_format)
            sheet.merge_range(row, 3, row, 7, '', table_format)
            row += 1

        material_headers = [
            'BOPP',
            'BOPET',
            'MET-BOPP',
            'MET-BOPET',
            'PVDC',
            'MATTE-BOPP',
            'BOPA'
        ]

        start_col = 10

        sheet.merge_range(5, start_col, 5, start_col + 6,
                          'Total approved slitted wieght ( Material type wise ) KGS',
                          bold_format)

        col = start_col

        for material in material_headers:
            sheet.write(6, col, material, header_format)
            sheet.write(7, col, '', table_format)
            col += 1

        customer_headers = [
            'CUSTOMER NAME',
            'BOPP(KGS)',
            'BOPET(KGS)',
            'MET-BOPP(KGS)',
            'MET-BOPET(KGS)',
            'MATTE-BOPP(KGS)',
            'BOPA(KGS)',
            'PVDC(KGS)',
        ]

        customer_row = 20

        col = 0

        for header in customer_headers:
            sheet.write(customer_row, col, header, header_format)
            col += 1

        customers = [
            'VINS PLASTICS',
            'ST.JOHNS',
            'CCL',
            'TORO',
            'TAMPER GUARD',
            'VISION FOOD',
            'MULTIWEB',
            'BULLDOG',
            'FGF',
            'SWEETS FROM THE EARTH',
            'VANSAN',
            'HELIX(TOLL SLITTING)',
            'FASPAC',
            'PLASTIXX',
            'POLYTARP',
            'TEMPO',
        ]

        customer_row += 1

        for customer in customers:

            sheet.write(customer_row, 0, customer, table_format)

            for col in range(1, 8):
                sheet.write(customer_row, col, '', table_format)

            customer_row += 1
        


        sheet2 = workbook.add_worksheet('Waste Analysis')

        sheet2.set_column('A:Z', 18)

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
        })

        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#F2E5B7',
        })

        table_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })

        bold_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })



        sheet2.merge_range('A1:Z1', 'WASTE ANALYSIS MATERIAL TYPE WISE', title_format)

        materials = [
            'BOPP',
            'BOPET',
            'MET-BOPP',
            'PVDC',
            'MET-BOPET',
            'MATTE-BOPP',
            'BOPA',
        ]

        labels = [
            'Slitting Input (Kgs)',
            'Slitting Output (Kgs)',
            'Approved Output (SOLD)\n(Kgs)',
            'Offcut Qty (Kgs)\n(Useable/back to stock)',
            'Output Efficiency (%)',
            'Total Waste (kgs)',
            'Waste %',
            'Trim Waste (Kgs)',
            'Trim Waste (%)',
            'Other Waste (kg) (non-usable\ndue to insufficient length or roll damage)',
            'Other Waste (%)',
            'Remarks if any',
        ]


        positions = [
            (3, 0),    # BOPP
            (3, 6),    # BOPET
            (3, 12),   # MET-BOPP
            (3, 18),   # PVDC
            (18, 0),   # MET-BOPET
            (18, 6),   # MATTE-BOPP
            (18, 12),  # BOPA
        ]

        for index, material in enumerate(materials):

            start_row, start_col = positions[index]


            sheet2.merge_range(
                start_row,
                start_col,
                start_row,
                start_col + 4,
                f'MIS SLITTING {material} {self.month.upper() if self.month else ""} {self.year or ""}',
                header_format
            )

            row = start_row + 1

            for label in labels:

                sheet2.merge_range(
                    row,
                    start_col,
                    row,
                    start_col + 2,
                    label,
                    bold_format
                )

                sheet2.merge_range(
                    row,
                    start_col + 3,
                    row,
                    start_col + 4,
                    '',
                    table_format
                )

                row += 1

        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'MIS_Slitting_Report.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype':
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
