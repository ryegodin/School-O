# Daily CGS Services: Usage Report
# Developed by Rye Godin

# Send on Friday,

# Database Imports
import datetime as DT
import smtplib
from datetime import date

# Emailer Imports
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid

import cx_Oracle  # Requires additional package installation 'python3.9 pip -m install cx_Oracle'

# Reference Times
d = date.today()
wago = d - DT.timedelta(days=7)
mago = d - DT.timedelta(days=30)
yago = d - DT.timedelta(days=365)
today = d.strftime("%y-%m-%d")
week_ago = wago.strftime("%y-%m-%d")
month_ago = mago.strftime("%y-%m-%d")
year_ago = yago.strftime("%y-%m-%d")

# Week Number based on Date (For Weekly Query)
week_num_td = int(d.strftime("%W"))
week_num_wa = int(wago.strftime("%W"))
week_num_ma = int(mago.strftime("%W"))
week_num_ya = int(yago.strftime("%W"))

# Special Case for Month of January. Week Number always needs to be increasing.
if week_num_ma > week_num_td:
    week_range_start = week_num_td
    week_range_end = week_num_ma
else:
    week_range_start = week_num_ma
    week_range_end = week_num_td


# Connection Class
class Database:
    def __init__(self, _hostname, _port, _user, _password, _service_name):
        self.hostname = _hostname
        self.port = _port
        self.user = _user
        self.password = _password
        self.service_name = _service_name

        self.connection_info = {
            'host': self.hostname,
            'port': self.port,
            'user': self.user,
            'pass': self.password,
            'service_name': self.service_name
        }

        self.connection_string = '{user}/{pass}@{host}:{port}/{service_name}'.format(**self.connection_info)
        self.connection = None

    def connect(self):
        self.connection = cx_Oracle.connect(self.connection_string)

    def close(self):
        self.connection.close()

    def query(self, query):
        return self.connection.cursor().execute(query)


## Database Info
hostname = 's-bsc-uiorprd2a.nrn.NRCan.gc.ca'
port = '****'
user = 'reader'
password = '****'
service = '***'
service_name = 'GEODB.NRCan.gc.ca'

# Connection Initialization
db = Database(hostname, port, user, password, service_name)
db.connect()

## PAA Tools | Daily Query
print("[PAA Tools]: Querying results... (2-5 minutes)")
# Number of direct users of CGS data products
query_direct_gcs_user = "select count(distinct b.customer_id) from ngis.requests b " \
                        "inner join ngis.request_items c on b.request_id = c.request_id " \
                        f"where to_char(b.request_date, 'yy-mm-dd') = '{today}' " \
                        "and (c.request_type != 'BBS' or c.item_code not in ('4','100','Z2'))"

# Number of requests for CGS data products and services
query_request_cgs = "select count(distinct b.request_id) from ngis.requests b " \
                    "INNER JOIN ngis.request_items c on b.request_id = c.request_id " \
                    "where b.customer_id not in ('5995','6167','6168','6169','6170','23337') " \
                    "and c.item_code not in('Z2','100','83') " \
                    f"and to_char(b.request_date, 'yy-mm-dd') = '{today}'"

# Number of active (submitted at-least one job) PPP users (Daily Amount)
query_ppp_user = "select count(distinct b.customer_id) " \
                 "from ngis.requests b inner join ngis.request_items c on b.request_id = c.request_id " \
                 f"where to_char(b.request_date, 'yy-mm-dd') = '{today}' " \
                 "and c.request_type = 'SOFTW' and c.ITEM_CODE in ('45','53','56')"

# Number of GNSS data and product files retrieved
query_gnss_data_product = "select round(sum(b.UNITS)) from ngis.REQUESTS a " \
                          "INNER JOIN ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                          f"where to_char(a.request_date, 'yy-mm-dd') = '{today}' " \
                          "and b.description like '%Raw%'"

# Number of precise orbit and clock products retrieved from CACS
query_orbit_and_clock = "select round(sum(b.UNITS)) from ngis.REQUESTS a " \
                        "INNER JOIN ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                        f"where to_char(a.request_date, 'yy-mm-dd') = '{today}' " \
                        "and (b.request_type = 'BBS' and b.description not like '%Raw%' and b.description not like '%BROADCAST%')"

# Number of Files Successfully Processed with CSRS-PPP
query_files_ppp = "select round(sum(b.UNITS)) from ngis.REQUESTS a " \
                  "INNER JOIN ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                  f"where to_char(a.REQUEST_DATE, 'yy-mm-dd') = '{today}' " \
                  "and (b.request_type = 'SOFTW' and b.ITEM_CODE in ('45','53','56'))"

results_direct_gcs_user = db.query(query_direct_gcs_user)
results_request_cgs = db.query(query_request_cgs)
results_ppp_user = db.query(query_ppp_user)
results_gnss_data_product = db.query(query_gnss_data_product)
results_orbit_and_clock = db.query(query_orbit_and_clock)
results_files_ppp = db.query(query_files_ppp)

for daily1 in results_direct_gcs_user:
    res_dir_gcs_user_d = daily1[0]
for daily2 in results_request_cgs:
    res_req_cgs_d = daily2[0]
for daily3 in results_ppp_user:
    res_ppp_user_d = daily3[0]
for daily4 in results_gnss_data_product:
    res_gnss_data_prod_d = daily4[0]
for daily5 in results_orbit_and_clock:
    res_orb_clock_d = daily5[0]
for daily6 in results_files_ppp:
    res_files_ppp_d = daily6[0]

## 7 Day Average Query
# Number of direct users of CGS data products (Weekly Average)
query_direct_gcs_user_w = "select count(distinct b.customer_id) from ngis.requests b " \
                          "inner join ngis.request_items c on b.request_id = c.request_id " \
                          f"where to_char(b.request_date, 'yy-mm-dd') > '{week_ago}' " \
                          f"and to_char(b.request_date, 'yy-mm-dd') <= '{today}' " \
                          "and (c.request_type != 'BBS' or c.item_code not in ('4','100','Z2'))"

# Number of requests for CGS data products and services
query_request_cgs_w = "select count(distinct b.request_id) from ngis.requests b " \
                      "INNER JOIN ngis.request_items c on b.request_id = c.request_id " \
                      "where b.customer_id not in ('5995','6167','6168','6169','6170','23337') " \
                      "and c.item_code not in('Z2','100','83') " \
                      f"and to_char(b.request_date, 'yy-mm-dd') > '{week_ago}' " \
                      f"and to_char(b.request_date, 'yy-mm-dd') <= '{today}'"

# Number of active (submitted at-least one job) PPP users (Weekly Average)
query_ppp_user_w = "select count(distinct a.CUSTOMER_ID) " \
                   "from ngis.REQUESTS a inner join ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                   f"where TO_NUMBER(TO_CHAR(a.request_date,'ww')) >= '{week_num_wa}' " \
                   f"and to_char(a.request_date, 'yy-mm-dd') > '{week_ago}' " \
                   f"and to_char(a.request_date, 'yy-mm-dd') <= '{today}' " \
                   "and b.request_type = 'SOFTW' and b.ITEM_CODE in ('45','53','56')"

# Number of GNSS data and product files retrieved
query_gnss_data_product_w = "select round(sum(b.UNITS)) from ngis.REQUESTS a " \
                            "INNER JOIN ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                            f"where to_char(a.request_date, 'yy-mm-dd') > '{week_ago}' " \
                            f"and to_char(a.request_date, 'yy-mm-dd') <= '{today}' " \
                            "and b.description like '%Raw%'"

# Number of precise orbit and clock products retrieved from CACS
query_orbit_and_clock_w = "select round(sum(b.UNITS)) from ngis.REQUESTS a " \
                          "INNER JOIN ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                          f"where to_char(a.request_date, 'yy-mm-dd') > '{week_ago}' " \
                          f"and to_char(a.request_date, 'yy-mm-dd') <= '{today}' " \
                          "and (b.request_type = 'BBS' and b.description not like '%Raw%' and b.description not like '%BROADCAST%')"

# Number of Files Successfully Processed with CSRS-PPP
query_files_ppp_w = "select round(sum(b.UNITS)) from ngis.REQUESTS a " \
                    "INNER JOIN ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                    f"where to_char(a.REQUEST_DATE, 'yy-mm-dd') > '{week_ago}' " \
                    f"and to_char(a.REQUEST_DATE, 'yy-mm-dd') <= '{today}' " \
                    "and (b.request_type = 'SOFTW' and b.ITEM_CODE in ('45','53','56'))"

results_direct_gcs_user_w = db.query(query_direct_gcs_user_w)
results_request_cgs_w = db.query(query_request_cgs_w)
results_ppp_user_w = db.query(query_ppp_user_w)
results_gnss_data_product_w = db.query(query_gnss_data_product_w)
results_orbit_and_clock_w = db.query(query_orbit_and_clock_w)
results_files_ppp_w = db.query(query_files_ppp_w)

for weekly1 in results_direct_gcs_user_w:
    res_dir_gcs_user_w = round(weekly1[0])
for weekly2 in results_request_cgs_w:
    res_req_cgs_w = round(weekly2[0] / 7)
for weekly3 in results_ppp_user_w:
    res_ppp_user_w = round(weekly3[0])
for weekly4 in results_gnss_data_product_w:
    res_gnss_data_prod_w = round(weekly4[0] / 7)
for weekly5 in results_orbit_and_clock_w:
    res_orb_clock_w = round(weekly5[0] / 7)
for weekly6 in results_files_ppp_w:
    res_files_ppp_w = round(weekly6[0] / 7)

## 30 Day Average Query | Results may take longer during January due to week numbers being opposite position for loop.
# Number of direct users of CGS data products (Weekly Average)

gcs_user_m = []

for week in range(1, 5):
    start = d - DT.timedelta(days=7*week)
    end = d - DT.timedelta(days=7*week) + DT.timedelta(days=6)
    start_form = start.strftime("%y-%m-%d")
    end_form = end.strftime("%y-%m-%d")

    query_direct_gcs_user_m = "select count(distinct b.customer_id) from ngis.requests b " \
                              "inner join ngis.request_items c on b.request_id = c.request_id " \
                              f"and to_char(b.request_date, 'yy-mm-dd') >= '{start_form}' " \
                              f"and to_char(b.request_date, 'yy-mm-dd') <= '{end_form}' " \
                              "and (c.request_type != 'BBS' or c.item_code not in ('4','100','Z2'))"
    results_direct_gcs_user_m = db.query(query_direct_gcs_user_m)
    for gcs_monthly in results_direct_gcs_user_m:
        gcs_user_m.append(int(gcs_monthly[0]))
res_dir_gcs_user_m = round(sum(gcs_user_m) / len(gcs_user_m))

# Number of requests for CGS data products and services
query_request_cgs_m = "select count(distinct b.request_id) from ngis.requests b " \
                      "INNER JOIN ngis.request_items c on b.request_id = c.request_id " \
                      "where b.customer_id not in ('5995','6167','6168','6169','6170','23337') " \
                      "and c.item_code not in('Z2','100','83') " \
                      f"and to_char(b.request_date, 'yy-mm-dd') >= '{month_ago}' " \
                      f"and to_char(b.request_date, 'yy-mm-dd') <= '{today}'"

# Number of active (submitted at-least one job) PPP users (Weekly Average)
ppp_user_m = []
for week in range(1,5):
    start = d - DT.timedelta(days=7*week)
    end = d - DT.timedelta(days=7*week) + DT.timedelta(days=6)
    start_form = start.strftime("%y-%m-%d")
    end_form = end.strftime("%y-%m-%d")

    query_ppp_user_m = "select count(distinct a.CUSTOMER_ID), count(a.REQUEST_ID) " \
                       "from ngis.REQUESTS a inner join ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                       f"and to_char(a.request_date, 'yy-mm-dd') >= '{start_form}' " \
                       f"and to_char(a.request_date, 'yy-mm-dd') <= '{end_form}' " \
                       "and b.request_type = 'SOFTW' and b.ITEM_CODE in ('45','53','56')"
    results_ppp_user_m = db.query(query_ppp_user_m)
    for ppp_monthly in results_ppp_user_m:
        ppp_user_m.append(int(ppp_monthly[0]))
res_ppp_user_m = round(sum(ppp_user_m)/len(ppp_user_m))

# Number of GNSS data and product files retrieved
query_gnss_data_product_m = "select round(sum(b.UNITS)) from ngis.REQUESTS a " \
                            "INNER JOIN ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                            f"where to_char(a.request_date, 'yy-mm-dd') >= '{month_ago}' " \
                            f"and to_char(a.request_date, 'yy-mm-dd') <= '{today}' " \
                            "and b.description like '%Raw%'"

# Number of precise orbit and clock products retrieved from CACS
query_orbit_and_clock_m = "select round(sum(b.UNITS)) from ngis.REQUESTS a " \
                          "INNER JOIN ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                          f"where to_char(a.request_date, 'yy-mm-dd') >= '{month_ago}' " \
                          f"and to_char(a.request_date, 'yy-mm-dd') <= '{today}' " \
                          "and (b.request_type = 'BBS' and b.description not like '%Raw%' and b.description not like '%BROADCAST%')"

# Number of Files Successfully Processed with CSRS-PPP
query_files_ppp_m = "select round(sum(b.UNITS)) from ngis.REQUESTS a " \
                    "INNER JOIN ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                    f"where to_char(a.REQUEST_DATE, 'yy-mm-dd') >= '{month_ago}' " \
                    f"and to_char(a.REQUEST_DATE, 'yy-mm-dd') <= '{today}' " \
                    "and (b.request_type = 'SOFTW' and b.ITEM_CODE in ('45','53','56'))"

results_request_cgs_m = db.query(query_request_cgs_m)
results_gnss_data_product_m = db.query(query_gnss_data_product_m)
results_orbit_and_clock_m = db.query(query_orbit_and_clock_m)
results_files_ppp_m = db.query(query_files_ppp_m)

for monthly1 in results_request_cgs_m:
    res_req_cgs_m = round(monthly1[0] / 30)
for monthly2 in results_gnss_data_product_m:
    res_gnss_data_prod_m = round(monthly2[0] / 30)
for monthly3 in results_orbit_and_clock_m:
    res_orb_clock_m = round(monthly3[0] / 30)
for monthly4 in results_files_ppp_m:
    res_files_ppp_m = round(monthly4[0] / 30)

## 365 Day Average Query
# Number of direct users of CGS data products (Weekly Average)
gcs_user_y = []
for week in range(1, 53):
    start = d - DT.timedelta(days=7*week)
    end = d - DT.timedelta(days=7*week) + DT.timedelta(days=6)
    start_form = start.strftime("%y-%m-%d")
    end_form = end.strftime("%y-%m-%d")

    query_direct_gcs_user_y = "select count(distinct b.customer_id) from ngis.requests b " \
                              "inner join ngis.request_items c on b.request_id = c.request_id " \
                              f"and to_char(b.request_date, 'yy-mm-dd') >= '{start_form}' " \
                              f"and to_char(b.request_date, 'yy-mm-dd') <= '{end_form}' " \
                              "and (c.request_type != 'BBS' or c.item_code not in ('4','100','Z2'))"
    results_direct_gcs_user_y = db.query(query_direct_gcs_user_y)
    for gcs_yearly in results_direct_gcs_user_y:
        gcs_user_y.append(int(gcs_yearly[0]))
res_dir_gcs_user_y = round(sum(gcs_user_y) / len(gcs_user_y))

# Number of requests for CGS data products and services
query_request_cgs_y = "select count(distinct b.request_id) from ngis.requests b " \
                      "INNER JOIN ngis.request_items c on b.request_id = c.request_id " \
                      "where b.customer_id not in ('5995','6167','6168','6169','6170','23337') " \
                      "and c.item_code not in('Z2','100','83') " \
                      f"and to_char(b.request_date, 'yy-mm-dd') >= '{year_ago}' " \
                      f"and to_char(b.request_date, 'yy-mm-dd') <= '{today}'"

# Number of active (submitted atleast one job) PPP users (Weekly Average)
ppp_user_y = []
for week in range(1,53):
    start = d - DT.timedelta(days=7*week)
    end = d - DT.timedelta(days=7*week) + DT.timedelta(days=6)
    start_form = start.strftime("%y-%m-%d")
    end_form = end.strftime("%y-%m-%d")

    query_ppp_user_y = "select count(distinct a.CUSTOMER_ID), count(a.REQUEST_ID) " \
                       "from ngis.REQUESTS a inner join ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                       f"and to_char(a.request_date, 'yy-mm-dd') >= '{start_form}' " \
                       f"and to_char(a.request_date, 'yy-mm-dd') <= '{end_form}' " \
                       "and b.request_type = 'SOFTW' and b.ITEM_CODE in ('45','53','56')"

    results_ppp_user_y = db.query(query_ppp_user_y)
    for ppp_yearly in results_ppp_user_y:
        ppp_user_y.append(int(ppp_yearly[0]))

res_ppp_user_y = round(sum(ppp_user_y)/len(ppp_user_y))

# Number of GNSS data and product files retrieved
query_gnss_data_product_y = "select round(sum(b.UNITS)) from ngis.REQUESTS a " \
                            "INNER JOIN ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                            f"where to_char(a.request_date, 'yy-mm-dd') >= '{year_ago}' " \
                            f"and to_char(a.request_date, 'yy-mm-dd') <= '{today}' " \
                            "and b.description like '%Raw%'"

# Number of precise orbit and clock products retrieved from CACS
query_orbit_and_clock_y = "select round(sum(b.UNITS)) from ngis.REQUESTS a " \
                          "INNER JOIN ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                          f"where to_char(a.request_date, 'yy-mm-dd') >= '{year_ago}' " \
                          f"and to_char(a.request_date, 'yy-mm-dd') <= '{today}' " \
                          "and (b.request_type = 'BBS' and b.description not like '%Raw%' and b.description not like '%BROADCAST%')"

# Number of Files Successfully Processed with CSRS-PPP
query_files_ppp_y = "select round(sum(b.UNITS)) from ngis.REQUESTS a " \
                    "INNER JOIN ngis.REQUEST_ITEMS b on a.REQUEST_ID = b.REQUEST_ID " \
                    f"where to_char(a.REQUEST_DATE, 'yy-mm-dd') >= '{year_ago}' " \
                    f"and to_char(a.REQUEST_DATE, 'yy-mm-dd') <= '{today}' " \
                    "and (b.request_type = 'SOFTW' and b.ITEM_CODE in ('45','53','56'))"

results_request_cgs_y = db.query(query_request_cgs_y)
results_gnss_data_product_y = db.query(query_gnss_data_product_y)
results_orbit_and_clock_y = db.query(query_orbit_and_clock_y)
results_files_ppp_y = db.query(query_files_ppp_y)

for yearly1 in results_request_cgs_y:
    res_req_cgs_y = round(yearly1[0] / 365)
for yearly2 in results_gnss_data_product_y:
    res_gnss_data_prod_y = round(yearly2[0] / 365)
for yearly3 in results_orbit_and_clock_y:
    res_orb_clock_y = round(yearly3[0] / 365)
for yearly4 in results_files_ppp_y:
    res_files_ppp_y = round(yearly4[0] / 365)

# Close Database
db.close()


############ EMAIL RESULTS ############
print("[PAA Tools]: Results will be emailed now.")

# 'my_address' shouldn't matter. Keep within NRCAN domain. For contact list, separate with commas.
my_address = 'ryan.godin@nrcan-rncan.gc.ca'
contact_list = 'ryan.godin@nrcan-rncan.gc.ca, brian.donahue@nrcan-rncan.gc.ca'

# For multiple contacts:
# contact_list = 'ryan.godin@nrcan-rncan.gc.ca, ryangodin@rogers.com'


def emailer():
    smtp = smtplib.SMTP(host='localhost')
    msg = EmailMessage()

    msg['From'] = my_address
    msg['To'] = contact_list
    msg['Subject'] = f'Daily CGS Services: Usage Report | {d}'

    # HTML of table to increase size for quick read. Normal text can go above <html> tag.
    msg.set_content("""\
              
        <html>
            <style type="text/css">
        .tg  {border - collapse:collapse;border-spacing:0;margin:0px auto;}
        .tg td{border - color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
          overflow:hidden;padding:10px 5px;word-break:normal;}
        .tg th{border - color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
          font-weight:normal;overflow:hidden;padding:10px 5px;word-break:normal;}
        .tg .tg-ho1w{font - family:serif !important;font-size:26px;text-align:center;vertical-align:top}
        .tg .tg-esqr{font - family:serif !important;font-size:26px;font-weight:bold;text-align:left;vertical-align:top}
        .tg .tg-a5gu{font - family:serif !important;font-size:26px;text-align:left;vertical-align:top}
        </style>
        <table class="tg">
        <thead>
          <tr>
            <th class="tg-ho1w" colspan="5"><span style="font-weight:bold">Daily CGS Services: Usage Report | """ + str(d) + """</span></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="tg-esqr">Metric</td>
            <td class="tg-esqr">Daily</td>
            <td class="tg-esqr">Weekly</td>
            <td class="tg-esqr">Monthly</td>
            <td class="tg-esqr">Yearly<br></td>
          </tr>
          <tr>
            <td class="tg-a5gu"># of Direct CGS Users (Weekly Averages)</td>
            <td class="tg-a5gu">""" + str(res_dir_gcs_user_d) + """</td>
            <td class="tg-a5gu">""" + str(res_dir_gcs_user_w) + """</td>
            <td class="tg-a5gu">""" + str(res_dir_gcs_user_m) + """</td>
            <td class="tg-a5gu">""" + str(res_dir_gcs_user_y) + """</td>
          </tr>
          <tr>
            <td class="tg-a5gu"># of Requests for CGS Products</td>
            <td class="tg-a5gu">""" + str(res_req_cgs_d) + """</td>
            <td class="tg-a5gu">""" + str(res_req_cgs_w) + """</td>
            <td class="tg-a5gu">""" + str(res_req_cgs_m) + """</td>
            <td class="tg-a5gu">""" + str(res_req_cgs_y) + """</td>
          </tr>
          <tr>
            <td class="tg-a5gu"># of PPP Users (Weekly Averages)</td>
            <td class="tg-a5gu">""" + str(res_ppp_user_d) + """</td>
            <td class="tg-a5gu">""" + str(res_ppp_user_w) + """</td>
            <td class="tg-a5gu">""" + str(res_ppp_user_m) + """</td>
            <td class="tg-a5gu">""" + str(res_ppp_user_y) + """</td>
          </tr>
          <tr>
            <td class="tg-a5gu"># of Files Processed with PPP</td>
            <td class="tg-a5gu">""" + str(res_files_ppp_d) + """</td>
            <td class="tg-a5gu">""" + str(res_files_ppp_w) + """</td>
            <td class="tg-a5gu">""" + str(res_files_ppp_m) + """</td>
            <td class="tg-a5gu">""" + str(res_files_ppp_y) + """</td>
          </tr>
          <tr>
            <td class="tg-a5gu"># of GNSS RINEX File Downloads</td>
            <td class="tg-a5gu">""" + str(res_gnss_data_prod_d) + """</td>
            <td class="tg-a5gu">""" + str(res_gnss_data_prod_w) + """</td>
            <td class="tg-a5gu">""" + str(res_gnss_data_prod_m) + """</td>
            <td class="tg-a5gu">""" + str(res_gnss_data_prod_y) + """</td>
          </tr>
          <tr>
            <td class="tg-a5gu"># of Retrieved Orbit / Clock Products from CACS</td>
            <td class="tg-a5gu">""" + str(res_orb_clock_d) + """</td>
            <td class="tg-a5gu">""" + str(res_orb_clock_w) + """</td>
            <td class="tg-a5gu">""" + str(res_orb_clock_m) + """</td>
            <td class="tg-a5gu">""" + str(res_orb_clock_y) + """</td>
          </tr>
        </tbody>
        </table>
    """.format(), subtype='html')

    smtp.send_message(msg)
    del msg
    smtp.quit()


emailer()
