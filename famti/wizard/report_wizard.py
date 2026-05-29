import io
import base64
import xlsxwriter
from odoo import models, fields
from datetime import date, datetime
from collections import defaultdict

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
                sheet.write(row, 11,lot.core_selection_id or '',cell_format)
                sheet.write(row, 12,lot.length_val or '',cell_format)
                sheet.write(row, 13,lot.product_qty or '',number_format)
                sheet.write(row, 14,lot.product_qty or '',number_format)
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

    def _get_year_selection(self):
        current_year = datetime.now().year

        years = []
        for year in range(current_year - 5, current_year + 10):
            years.append((str(year), str(year)))

        return years

    year = fields.Selection(
        selection=_get_year_selection,
        string="Year",
        default=lambda self: str(datetime.now().year)
    )

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
        sheet.merge_range('A5:H5', 'MIS MONTHLY REPORT', header_format)
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
            (3, 0), 
            (3, 6),  
            (3, 12),  
            (3, 18), 
            (18, 0),  
            (18, 6),  
            (18, 12),  
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

class SlittingLogBookWizard(models.TransientModel):
    _name = 'slitting.log.book.wizard'
    _description = 'Slitting Log Book Report'

    start_date = fields.Date(
        string='Start Date'
    )

    end_date = fields.Date(
        string='End Date'
    )

    shift = fields.Selection([
        ('day', 'Day'),
        ('night', 'Night')
    ], string='Shift')

    supervisor = fields.Many2one(
        'hr.employee',
        string='Supervisor'
    )

    operator_id = fields.Many2one(
        'hr.employee',
        string='Operator'
    )

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        sheet = workbook.add_worksheet(
            'Slitting Log Book'
        )

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 16,
            'border': 1
        })

        sub_title = workbook.add_format({
            'bold': True,
            'align': 'left',
            'font_size': 11
        })

        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#D9D9D9',
            'font_size': 9,
            'text_wrap': True
        })

        text_format = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'align': 'left'
        })

        center_format = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'align': 'center'
        })

        amount_format = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'align': 'right',
            'num_format': '#,##0.00'
        })

        sheet.set_column('A:AJ', 18)

        sheet.merge_range(
            'A1:AJ2',
            'FAM Ti Inc Canada Slitting Log Book',
            title_format
        )

        row = 4

        sheet.write(row, 0, 'MONTH:', sub_title)
        sheet.write(row, 4, 'DATE:', sub_title)
        sheet.write(row, 8, 'SHIFT:', sub_title)
        sheet.write(row, 12, 'SUPERVISOR:', sub_title)
        sheet.write(row, 18, 'OPERATOR:', sub_title)

        sheet.write(
            row, 1,
            self.start_date.strftime('%B')
            if self.start_date else '',
            text_format
        )

        sheet.write(
            row, 5,
            str(self.start_date or ''),
            text_format
        )

        sheet.write(
            row, 9,
            dict(self._fields['shift'].selection).get(
                self.shift
            ) if self.shift else '',
            text_format
        )

        sheet.write(
            row, 13,
            self.supervisor.name or '',
            text_format
        )

        sheet.write(
            row, 19,
            self.operator_id.name or '',
            text_format
        )

        row += 2

        sheet.merge_range(
            row, 0,
            row, 25,
            'SLITTING DETAILS',
            header_format
        )

        sheet.merge_range(
            row, 26,
            row + 1, 33,
            'QC',
            header_format
        )

        sheet.merge_range(
            row, 34,
            row + 1, 35,
            'QA-HEAD',
            header_format
        )

        row += 1

        sheet.merge_range(
            row, 0,
            row, 10,
            'SLITTING INPUT',
            header_format
        )

        sheet.merge_range(
            row, 11,
            row, 25,
            'SLITTING OUTPUT',
            header_format
        )

        row += 1

        headers = [
            'S.NO',
            'DATE',
            'SHIFT',
            'Film Type',
            'Product CODE',
            'JUMBO ROLL NUMBER',
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
            'JOINT',
            'TREATMENT',
            'SALES ORDER',
            'BUYER',
            'TRIM WIDTH MM',
            'TRIM WEIGHT KG',
            'WASTE(KGS)',
            'OFFCUT - MM',
            'DYNE VALUE',
            'HAZE',
            'AVG.THICKNESS/JOINTS &BOTTOM',
            'DA NO./WDA',
            'CUSTOMER NAME',
            'GRADE',
            'DEFECT',
            'REMARK',
            'UPGRADATION',
            'REMARKS'
        ]

        col = 0

        for header in headers:

            sheet.write(
                row,
                col,
                header,
                header_format
            )

            col += 1

        row += 1

        domain = [
            ('is_slitting', '=', True)
        ]

        if self.start_date:
            domain.append((
                'date_start',
                '>=',
                self.start_date
            ))

        if self.end_date:
            domain.append((
                'date_start',
                '<=',
                self.end_date
            ))

        productions = self.env[
            'mrp.production'
        ].search(domain)

        sl_no = 1

        for rec in productions:

            component = rec.move_raw_ids[:1]

            lot = component.lot_ids[:1] if component else False

            jumbo_roll = lot.name if lot else ''

            thickness = getattr(
                lot,
                'thickness',
                ''
            )

            width = getattr(
                lot,
                'width_val',
                ''
            )

            length = getattr(
                lot,
                'length_val',
                ''
            )

            treatment = getattr(
                component.product_id,
                'treatment',
                ''
            ) if component else ''

            for serial_line in rec.serial_line_ids:

                sheet.write(row, 0,sl_no,center_format)
                sheet.write(row, 1,str(rec.date_start.date() if rec.date_start else ''),center_format)
                sheet.write(row, 2,dict(self._fields['shift'].selection).get(self.shift) if self.shift else '',center_format)
                sheet.write(row, 3,rec.product_id.categ_id.name or '',text_format)
                sheet.write(row, 4,rec.product_id.default_code or '',text_format)
                sheet.write(row, 5,jumbo_roll,text_format)
                sheet.write(row, 6,thickness,center_format)
                sheet.write(row, 7,width,center_format)
                sheet.write(row, 8,length,center_format)
                sheet.write(row, 9,component.quantity if component else 0.0,amount_format)
                sheet.write(row, 10,treatment,text_format)
                sheet.write(row, 11,serial_line.serial_number or '',text_format)
                sheet.write(row, 12,serial_line.width or '',center_format)
                sheet.write(row, 13,serial_line.core_id or '',center_format)
                sheet.write(row, 14,serial_line.length or '',center_format)
                sheet.write(row, 15,serial_line.total_input or 0.0,amount_format)
                sheet.write(row, 16,serial_line.quantity or 0.0,amount_format)
                sheet.write(row, 17,serial_line.quantity or 0.0,amount_format)
                sheet.write(row, 18, '',center_format)
                sheet.write(row, 19, '',text_format)
                sale_order = self.env['sale.order'].search([('name', '=', rec.origin)], limit=1)
                sheet.write(row, 20, sale_order.name or '', text_format)
                sheet.write(row, 21, sale_order.partner_id.name or '', text_format)
                sheet.write(row, 22, '', text_format)
                sheet.write(row, 23, '', text_format)
                sheet.write(row, 24, '', text_format)
                sheet.write(row, 25, '', text_format)

                sheet.write(row, 26, '', text_format)
                sheet.write(row, 27, '', text_format)
                sheet.write(row, 28, '', text_format)
                sheet.write(row, 29, '', text_format)
                sheet.write(row, 30, '', text_format)
                sheet.write(row, 31, serial_line.grade_type or '', center_format)
                sheet.write(row, 32, '', text_format)
                sheet.write(row, 33, '', text_format)

                sheet.write(row, 34, '', text_format)
                sheet.write(row, 35, '', text_format)

                row += 1
                sl_no += 1

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(
            output.read()
        )

        output.close()

        attachment = self.env[
            'ir.attachment'
        ].create({
            'name': 'Slitting_Log_Book.xlsx',
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
    


class InventoryAgingReportWizard(models.TransientModel):
    _name = 'inventory.aging.report.wizard'
    _description = 'Inventory Aging Report Wizard'

    product_ids = fields.Many2many(
        'product.product',
        string='Products'
    )

    customer_ids = fields.Many2many(
        'res.partner',
        string='Customers'
    )

    location_ids = fields.Many2many(
        'stock.location',
        string='Locations'
    )

    start_date = fields.Date(
        string='Start Date'
    )

    end_date = fields.Date(
        string='End Date'
    )

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        sheet = workbook.add_worksheet(
            'Inventory Aging Report'
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

        sheet.set_column('A:A', 18)
        sheet.set_column('B:B', 40)
        sheet.set_column('C:C', 18)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 18)
        sheet.set_column('F:F', 18)
        sheet.set_column('G:G', 25)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 20)
        sheet.set_column('J:J', 30)
        sheet.set_column('K:K', 20)
        sheet.set_column('L:L', 30)

        sheet.merge_range(
            'A1:L2',
            'Inventory Aging Report',
            title_format
        )


        headers = [
            'Inventory ID',
            'Name',
            'THICKNESS MICRON',
            'WIDTH MM',
            'WIDTH INCHES',
            'LENGTH METERS',
            'NET WEIGHT PER ROLL (KGS)',
            'NO OF ROLLS',
            'TOTAL WEIGHT (KGS)',
            'CUSTOMER NAME',
            'Aging (No. of days)',
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


        domain = []

        if self.product_ids:
            domain.append((
                'product_id',
                'in',
                self.product_ids.ids
            ))

        if self.start_date:
            domain.append((
                'create_date',
                '>=',
                self.start_date
            ))

        if self.end_date:
            domain.append((
                'create_date',
                '<=',
                self.end_date
            ))

        lots = self.env[
            'stock.lot'
        ].search(domain)

        row += 1

        for lot in lots:

            quants = self.env[
                'stock.quant'
            ].search([
                ('lot_id', '=', lot.id),
                ('quantity', '>', 0)
            ])

            if self.location_ids:
                quants = quants.filtered(
                    lambda q:
                    q.location_id.id in
                    self.location_ids.ids
                )

            qty = sum(
                quants.mapped('quantity')
            )

            if qty <= 0:
                continue

            create_date = (
                lot.create_date.date()
                if lot.create_date else
                date.today()
            )

            aging_days = (
                date.today() - create_date
            ).days

            width_mm = (
                lot.width_val or 0.0
            )

            width_inches = round(
                width_mm / 25.4,
                2
            ) if width_mm else 0.0

            net_weight = (
                lot.product_qty or 0.0
            )

            quant_domain = [
                ('product_id', '=', lot.product_id.id),
                ('quantity', '>', 0)
            ]

            if self.location_ids:
                quant_domain.append((
                    'location_id',
                    'in',
                    self.location_ids.ids
                ))

            total_weight = sum(
                self.env['stock.quant'].search(
                    quant_domain
                ).mapped('quantity')
            )

            customer_name = ''

            if hasattr(lot, 'partner_id') and lot.partner_id:
                customer_name = (
                    lot.partner_id.name
                )

            sheet.write(
                row,
                0,
                lot.name or '',
                text_format
            )

            sheet.write(
                row,
                1,
                lot.product_id.name or '',
                text_format
            )

            sheet.write(
                row,
                2,
                lot.thickness or 0.0,
                center_format
            )

            sheet.write(
                row,
                3,
                width_mm,
                center_format
            )

            sheet.write(
                row,
                4,
                width_inches,
                center_format
            )

            sheet.write(
                row,
                5,
                lot.length_val or 0.0,
                center_format
            )

            sheet.write(
                row,
                6,
                net_weight,
                amount_format
            )

            sheet.write(
                row,
                7,
                qty,
                amount_format
            )

            sheet.write(
                row,
                8,
                total_weight,
                amount_format
            )

            sheet.write(
                row,
                9,
                customer_name,
                text_format
            )

            sheet.write(
                row,
                10,
                aging_days,
                center_format
            )

            sheet.write(
                row,
                11,
                '',
                text_format
            )

            row += 1

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(
            output.read()
        )

        output.close()

        attachment = self.env[
            'ir.attachment'
        ].create({
            'name': 'Inventory_Aging_Report.xlsx',
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
    

class InventoryFilmTypeReportWizard(models.TransientModel):
    _name = 'inventory.film.type.report.wizard'
    _description = 'Inventory Film Type Report Wizard'

    location_ids = fields.Many2many(
        'stock.location',
        string='Locations'
    )

    start_date = fields.Date(
        string='Start Date'
    )

    end_date = fields.Date(
        string='End Date'
    )

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        sheet = workbook.add_worksheet(
            'Inventory Summary'
        )

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 14,
            'border': 1
        })

        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#D9D9D9',
            'font_size': 10
        })

        text_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'align': 'left'
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
            'bg_color': '#EFEFEF',
            'font_size': 10,
            'align': 'right',
            'num_format': '#,##0.00'
        })

        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:I', 18)

        sheet.merge_range(
            'A1:I2',
            'Sum of Net Weight (Kgs)',
            title_format
        )

        headers = [
            'Supplier Name',
            'Material Type',
            'Thickness',
            'Alox',
            'Bare',
            'MET',
            'GOLD MET',
            'PVDC',
            'Grand Total'
        ]

        row = 3

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)

        domain = [
            ('qty_available', '>', 0)
        ]

        if self.start_date:
            domain.append((
                'create_date',
                '>=',
                self.start_date
            ))

        if self.end_date:
            domain.append((
                'create_date',
                '<=',
                self.end_date
            ))

        products = self.env[
            'product.template'
        ].search(domain)

        grouped_data = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: {
                        'alox': 0.0,
                        'bare': 0.0,
                        'met': 0.0,
                        'gold_met': 0.0,
                        'pvdc': 0.0,
                    }
                )
            )
        )

        for product in products:

            qty = product.qty_available or 0.0

            if qty <= 0:
                continue

            supplier = ''

            if product.seller_ids:
                supplier = product.seller_ids[0].partner_id.name or ''

            material_type = product.categ_id.name or ''

            thickness = str(
                getattr(
                    product,
                    'thickness_val',
                    ''
                )
            )

            film_type = getattr(
                product,
                'film_type',
                ''
            )

            if not film_type:
                continue

            grouped_data[
                supplier
            ][material_type][thickness][film_type] += qty

        row += 1

        grand_alox = 0.0
        grand_bare = 0.0
        grand_met = 0.0
        grand_gold_met = 0.0
        grand_pvdc = 0.0
        grand_total = 0.0

        for supplier, materials in grouped_data.items():

            supplier_alox = 0.0
            supplier_bare = 0.0
            supplier_met = 0.0
            supplier_gold_met = 0.0
            supplier_pvdc = 0.0
            supplier_total = 0.0

            for material, thicknesses in materials.items():

                material_alox = 0.0
                material_bare = 0.0
                material_met = 0.0
                material_gold_met = 0.0
                material_pvdc = 0.0
                material_total = 0.0

                for thickness, values in thicknesses.items():

                    alox = values.get('alox', 0.0)
                    bare = values.get('bare', 0.0)
                    met = values.get('met', 0.0)
                    gold_met = values.get('gold_met', 0.0)
                    pvdc = values.get('pvdc', 0.0)

                    total = (
                        alox +
                        bare +
                        met +
                        gold_met +
                        pvdc
                    )

                    sheet.write(row, 0, supplier, text_format)
                    sheet.write(row, 1, material, text_format)
                    sheet.write(row, 2, thickness, text_format)
                    sheet.write(row, 3, alox, amount_format)
                    sheet.write(row, 4, bare, amount_format)
                    sheet.write(row, 5, met, amount_format)
                    sheet.write(row, 6, gold_met, amount_format)
                    sheet.write(row, 7, pvdc, amount_format)
                    sheet.write(row, 8, total, total_format)

                    material_alox += alox
                    material_bare += bare
                    material_met += met
                    material_gold_met += gold_met
                    material_pvdc += pvdc
                    material_total += total

                    row += 1

                sheet.write(row, 1, material + ' Total', header_format)
                sheet.write(row, 3, material_alox, total_format)
                sheet.write(row, 4, material_bare, total_format)
                sheet.write(row, 5, material_met, total_format)
                sheet.write(row, 6, material_gold_met, total_format)
                sheet.write(row, 7, material_pvdc, total_format)
                sheet.write(row, 8, material_total, total_format)

                supplier_alox += material_alox
                supplier_bare += material_bare
                supplier_met += material_met
                supplier_gold_met += material_gold_met
                supplier_pvdc += material_pvdc
                supplier_total += material_total

                row += 1

            sheet.write(row, 0, supplier + ' Total', header_format)
            sheet.write(row, 3, supplier_alox, total_format)
            sheet.write(row, 4, supplier_bare, total_format)
            sheet.write(row, 5, supplier_met, total_format)
            sheet.write(row, 6, supplier_gold_met, total_format)
            sheet.write(row, 7, supplier_pvdc, total_format)
            sheet.write(row, 8, supplier_total, total_format)

            grand_alox += supplier_alox
            grand_bare += supplier_bare
            grand_met += supplier_met
            grand_gold_met += supplier_gold_met
            grand_pvdc += supplier_pvdc
            grand_total += supplier_total

            row += 1

        sheet.write(row, 0, 'Grand Total', header_format)
        sheet.write(row, 3, grand_alox, total_format)
        sheet.write(row, 4, grand_bare, total_format)
        sheet.write(row, 5, grand_met, total_format)
        sheet.write(row, 6, grand_gold_met, total_format)
        sheet.write(row, 7, grand_pvdc, total_format)
        sheet.write(row, 8, grand_total, total_format)

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(
            output.read()
        )

        output.close()

        attachment = self.env[
            'ir.attachment'
        ].create({
            'name': 'Inventory_Film_Type_Report.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
