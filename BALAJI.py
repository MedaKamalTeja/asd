from flask import Flask, render_template, request, Response, session
import mysql.connector
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database configuration
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="local instance mysql83"
)
cursor = db.cursor()

@app.route('/')
def index():
    return render_template('index_db(new).html')

@app.route('/search', methods=['POST'])
def search():
    psi_id = request.form.get('psi_id')
    location = request.form.get('location')
    bu = request.form.get('BU')
    project = request.form.get('project')

    try:
        if psi_id and not (location or bu or project):
            cursor.execute("SELECT * FROM master_table WHERE `Employee Code` = %s", (psi_id,))
            manager_info = cursor.fetchone()

            if manager_info is None:
                return "Manager not found."

            query = "SELECT * FROM master_table WHERE `Reporting Manager` = %s"
            params = (psi_id,)
            cursor.execute(query, params)
            reportees = cursor.fetchall()
            print(reportees)

            reportee_psi_ids = [reportee[0] for reportee in reportees]
            attendance_query = "SELECT * FROM attendance_report WHERE `EmployeeCode` IN ({})".format(','.join(['%s'] * len(reportee_psi_ids)))

            cursor.execute(attendance_query, tuple(reportee_psi_ids))
            employee_attendance = cursor.fetchall()
            session['employee_attendance'] = employee_attendance

            return render_template('results(new).html', manager_info=manager_info, employee_attendance=employee_attendance)

        # elif location:
        #     query = "SELECT `Employee Code`, `Employee Name`, `Reporting Manager` FROM employee_master_data WHERE Location = %s"
        #     cursor.execute(query, (location,))
        #     employee_details = cursor.fetchall()
        #     session['employee_details'] = employee_details  # Storing data in session
        #     return render_template('search_result.html', employee_details=employee_details,
        #                            search_type="Employees working in location: "+ location)

        elif location:
            employee_query = """
                SELECT e.`Employee Code`, e.`Employee Name`, m.`Employee Name` AS `Reporting Manager`, e.`BU`
                FROM master_table e
                LEFT JOIN master_table m ON e.`Reporting Manager` = m.`Employee Code`
                WHERE e.Location = %s
            """
            cursor.execute(employee_query, (location,))
            employee_details = cursor.fetchall()
            session['employee_details'] = employee_details
            attendance_data = {}
            attendance_query = "SELECT EmployeeCode, TotalPresent, TotalAbsent, AbsentDates FROM attendance_report WHERE EmployeeCode IN (SELECT `Employee Code` FROM master_table WHERE Location = %s)"
            cursor.execute(attendance_query, (location,))
            attendance_records = cursor.fetchall()

            for record in attendance_records:
                attendance_data[record[0]] = {'TotalPresent': record[1], 'TotalAbsent': record[2],
                                              'AbsentDates': record[3]}

            for i, employee in enumerate(employee_details):
                employee_code = employee[0]

                if employee_code in attendance_data:
                    total_present = attendance_data[employee_code]['TotalPresent']
                    total_absent = attendance_data[employee_code]['TotalAbsent']
                    absent_dates = attendance_data[employee_code]['AbsentDates']
                    employee_details[i] += (total_present, total_absent, absent_dates)

                else:
                    employee_details[i] += ("", "", "")
            return render_template('search(new).html', employee_details=employee_details,
                                   search_type="Employees working under: " + location)


        elif project:
            query = "SELECT `Employee Code`, `Employee Name`, `Reporting Manager` FROM master_table WHERE Project = %s"
            cursor.execute(query, (project,))
            employee_details = cursor.fetchall()
            session['employee_details'] = employee_details  # Storing data in session
            return render_template('search(new).html', employee_details=employee_details,
                                   search_type="Employees working in: " + project)

        # elif bu:
        #     query = "SELECT `Employee Code`, `Employee Name`, `Reporting Manager` FROM employee_master_data WHERE BU = %s"
        #     cursor.execute(query, (bu,))
        #     employee_details = cursor.fetchall()
        #     session['employee_details'] = employee_details  # Storing data in session
        #     return render_template('search_result.html', employee_details=employee_details,
        #                            search_type="Employees working in BU: " + bu)

        elif bu:
            # employee_query = "SELECT `Employee Code`, `Employee Name`, `Reporting Manager`, `Location` FROM master_table WHERE BU = %s"
            employee_query = """
                SELECT e.`Employee Code`, e.`Employee Name`, m.`Employee Name` AS `Reporting Manager`, e.`Location`
                FROM master_table e
                LEFT JOIN master_table m ON e.`Reporting Manager` = m.`Employee Code`
                WHERE e.BU = %s
            """
            cursor.execute(employee_query, (bu,))
            employee_details = cursor.fetchall()
            session['employee_details'] = employee_details
            attendance_data = {}
            attendance_query = "SELECT EmployeeCode, TotalPresent, TotalAbsent, AbsentDates FROM attendance_report WHERE EmployeeCode IN (SELECT `Employee Code` FROM master_table WHERE BU = %s)"
            cursor.execute(attendance_query, (bu,))
            attendance_records = cursor.fetchall()

            for record in attendance_records:
                attendance_data[record[0]] = {'TotalPresent': record[1], 'TotalAbsent': record[2],
                                              'AbsentDates': record[3]}

            for i, employee in enumerate(employee_details):
                employee_code = employee[0]

                if employee_code in attendance_data:
                    total_present = attendance_data[employee_code]['TotalPresent']
                    total_absent = attendance_data[employee_code]['TotalAbsent']
                    absent_dates = attendance_data[employee_code]['AbsentDates']
                    employee_details[i] += (total_present, total_absent, absent_dates)

                else:
                    employee_details[i] += ("", "", "")
            return render_template('search(new).html', employee_details=employee_details,
                                   search_type="Employees working under BU: " + bu)

        else:
            return "Error: invalid search request"

    except Exception as e:
        return f"An error occurred: {str(e)}"



# @app.route('/download_csv')
# def download_csv():
#     try:
#         employee_details = session.get('employee_details')
#
#         if not employee_details:
#             return "No data to download."
#
#         csv_output = StringIO()
#         csv_writer = csv.writer(csv_output)
#         csv_writer.writerow(['Employee Code', 'Employee Name', 'Reporting Manager', 'Location', 'Total Present', 'Total Absent'])
#
#         for employee in employee_details:
#             csv_writer.writerow([employee[0], employee[1], employee[2], employee[3], employee[4], employee[5]])
#
#         return Response(
#             csv_output.getvalue(),
#             mimetype='text/csv',
#             headers={'Content-Disposition': 'attachment;filename=employee_details.csv'}
#         )
#
#     except Exception as e:
#         return f"An error occurred while downloading CSV: {str(e)}"





# @app.route('/download_csv')
# def download_csv():
#     try:
#         employee_details = session.get('employee_details')
#
#         if not employee_details:
#             return "No data to download."
#
#         csv_output = StringIO()
#         csv_writer = csv.writer(csv_output)
#
#         # Determine the search type (BU or Location) and extract the value
#         search_type = session.get('search_type', '')
#         search_value = search_type.split(': ')[-1]
#
#         # Write the header line to the CSV file
#         csv_writer.writerow(["Employees Working under {}".format(search_value)])
#
#         # Write the headings to the CSV file based on the search type
#         if search_type.startswith("Employees working in BU"):
#             headings = ['Employee Code', 'Employee Name', 'Reporting Manager', 'Location', 'Total Present',
#                         'Total Absent']
#         else:
#             headings = ['Employee Code', 'Employee Name', 'Reporting Manager', 'BU', 'Total Present', 'Total Absent']
#
#         # Write the headings to the CSV file
#         csv_writer.writerow(headings)
#
#         # Write the data rows to the CSV file
#         for employee in employee_details:
#             csv_writer.writerow([employee[0], employee[1], employee[2], employee[3], employee[4], employee[5]])
#
#         # Reset the StringIO object's file position to the beginning
#         csv_output.seek(0)
#
#         # Create a CSV download response including headings, header, and data
#         return Response(
#             csv_output.getvalue(),
#             mimetype='text/csv',
#             headers={'Content-Disposition': 'attachment;filename=employee_details.csv'}
#         )
#
#     except Exception as e:
#         return f"An error occurred while downloading CSV: {str(e)}"





@app.route('/download_csv')
def download_csv():
    try:
        employee_details = session.get('employee_details')

        if not employee_details:
            return "No data to download."

        csv_output = StringIO()
        csv_writer = csv.writer(csv_output)

        # Determine the search type (BU or Location) and extract the value
        search_type = session.get('search_type', '')
        search_value = search_type.split(': ')[-1]

        # Get the date range
        start_date = session.get('Mar-1')
        end_date = session.get('Mar-26')

        # Convert dates to string format
        start_date_str = start_date.strftime("%Y-%m-%d") if start_date else "01-Mar"
        end_date_str = end_date.strftime("%Y-%m-%d") if end_date else "26-Mar"

        # Write the header lines to the CSV file
        csv_writer.writerow(["Employees Working under {}".format(search_value)])
        csv_writer.writerow(["Date Range: {} to {}".format(start_date_str, end_date_str)])

        # Write the headings to the CSV file based on the search type
        if search_type.startswith("Employees working in BU"):
            headings = ['Employee Code', 'Employee Name', 'Reporting Manager', 'Location', 'Total Present',
                        'Total Absent']
        else:
            headings = ['Employee Code', 'Employee Name', 'Reporting Manager', 'Location', 'Total Present', 'Total Absent']

        # Write the headings to the CSV file
        csv_writer.writerow(headings)

        # Write the data rows to the CSV file
        for employee in employee_details:
            csv_writer.writerow([employee[0], employee[1], employee[2], employee[3], employee[4], employee[5]])

        # Reset the StringIO object's file position to the beginning
        csv_output.seek(0)

        # Create a CSV download response including headings, header, and data
        return Response(
            csv_output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=employee_details.csv'}
        )

    except Exception as e:
        return f"An error occurred while downloading CSV: {str(e)}"




if __name__ == '__main__':
    app.run(debug=True)



