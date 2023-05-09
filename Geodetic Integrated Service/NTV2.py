#!/usr/bin/env python

# -------------------------------------------------------------------------------------------------------------------- #
#            Use of Canadian Geodetic Survey products and data is subject to the Open Government Licence - Canada      #
#                                  https://open.canada.ca/en/open-government-licence-canada                            #
# -------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------------------------------- #
#                                                                                                                      #
#                                              NRCan Geodetic Tools and Data: NTv2                                     #
#                                        For more information refer to the bottom of script                            #
#                                             Recommended Compatibility: Python 3.7+                                   #
#                                                                                                                      #
# -------------------------------------------------------------------------------------------------------------------- #

# Script info
# -----------
# __author__ = 'Ryan Godin'
# __copyright__ = '© His Majesty the King in Right of Canada, as represented by the Minister of Natural Resources,' \
#                 ' 2017-2023'
# __credits__ = 'Ryan Godin, Justin Farinaccio, Brian Donahue'
# __email__ = 'geodeticinformation-informationgeodesique@nrcan-rncan.gc.ca'
# __license__ = 'Open Government Licence - Canada'
# __maintainer__ = 'Ryan Godin'
# __status__ = 'Development'
# __version__ = '1.0.0'

import argparse
import json
import urllib.parse
from urllib.request import urlopen
import os
import sys
import zipfile
import shutil

try:
    assert sys.version_info >= (3, 5)
except AssertionError:
    sys.exit('ERROR: Must use Python 3.5.x or higher\n\t(see https://www.python.org/)')
try:
    import requests
except ImportError:
    sys.exit('ERROR: Must install Requests library\n\t(see https://requests.readthedocs.io/en/latest/)')
try:
    from requests_toolbelt.multipart.encoder import MultipartEncoder
except ImportError:
    sys.exit('ERROR: Must install Requests Toolbelt library\n\t(see https://toolbelt.readthedocs.io/en/latest/)')

coverage_and_grid = {
    'NTV2': {
        'Coverage': 'Canada',
        'From': 'NAD27',
        'To': 'NAD83(Original)',
    },
    'ABCSRSV4': {
        'Coverage': 'Alberta',
        'From': 'NAD83(Original)',
        'To': 'NAD83(CSRS) 2002',
    },
    'ABCSRSV7': {
        'Coverage': 'Alberta',
        'From': 'NAD83(Original)',
        'To': 'NAD83(CSRS) 2010',
    },
    'CRD27_00': {
        'Coverage': 'BC (CRD)',
        'From': 'NAD27',
        'To': 'NAD83(CSRS) 1997',
    },
    'CRD93_00': {
        'Coverage': 'BC (CRD)',
        'From': 'NAD83(Original)',
        'To': 'NAD83(CSRS) 1997',
    },
    'NVI93_05': {
        'Coverage': 'BC (Vancouver Island)',
        'From': 'NAD83(Original)',
        'To': 'NAD83(CSRS) 1997',
    },
    'BC_27_05': {
        'Coverage': 'British Columbia',
        'From': 'NAD27',
        'To': 'NAD83(CSRS) 2002',
    },
    'BC_93_05': {
        'Coverage': 'British Columbia',
        'From': 'NAD83(Original)',
        'To': 'NAD83(CSRS) 2002',
    },
    'NB7783v2': {
        'Coverage': 'New Brunswick',
        'From': 'ATS77',
        'To': 'NAD83(CSRS) 1997',
    },
    'NB2783_v2': {
        'Coverage': 'New Brunswick',
        'From': 'NAD27',
        'To': 'NAD83(CSRS) 1997',
    },
    'NLCSRSV4A': {
        'Coverage': 'Newfoundland(Island)',
        'From': 'NAD83(Original)',
        'To': 'NAD83(CSRS) 2010',
    },
    'GS7783': {
        'Coverage': 'Nova Scotia',
        'From': 'ATS77',
        'To': 'NAD83(Original)',
    },
    'NS778302': {
        'Coverage': 'Nova Scotia',
        'From': 'NAD27',
        'To': 'NAD83(CSRS) 2010',
    },
    'ON27CSv1': {
        'Coverage': 'Ontario',
        'From': 'NAD27',
        'To': 'NAD83(CSRS) 1997',
    },
    'ON76CSv1': {
        'Coverage': 'Ontario',
        'From': 'NAD27(MAY76)',
        'To': 'NAD83(CSRS) 1997',
    },
    'ON83CSv1': {
        'Coverage': 'Ontario',
        'From': 'NAD83(Original)',
        'To': 'NAD83(CSRS) 1997',
    },
    'TO27CSv1': {
        'Coverage': 'Ontario (Toronto)',
        'From': 'NAD27',
        'To': 'NAD83(CSRS) 1997',
    },
    'PE7783V2': {
        'Coverage': 'Prince Edward Island',
        'From': 'ATS77',
        'To': 'NAD83(CSRS) 1997',
    },
    'NA27SCRS': {
        'Coverage': 'Quebec',
        'From': 'NAD27',
        'To': 'NAD83(CSRS) 1997',
    },
    'CQ77SCRS': {
        'Coverage': 'Quebec',
        'From': 'NAD27(CGQ77)',
        'To': 'NAD83(CSRS) 1997',
    },
    'NA83SCRS': {
        'Coverage': 'Quebec',
        'From': 'NAD83(Original)',
        'To': 'NAD83(CSRS) 1997',
    },
    'SK27-98': {
        'Coverage': 'Saskatchewan',
        'From': 'NAD27',
        'To': 'NAD83(CSRS) 1997',
    },
    'SK83-98': {
        'Coverage': 'Saskatchewan',
        'From': 'NAD83(Original)',
        'To': 'NAD83(CSRS) 1997',
    }
}

# For formatting an appropriate table
max_grid_len = max(len(grid) for grid in coverage_and_grid.keys())
max_coverage_len = max(len(str(data['Coverage'])) for data in coverage_and_grid.values())
max_from_len = max(len(str(data['From'])) for data in coverage_and_grid.values())
max_to_len = max(len(str(data['To'])) for data in coverage_and_grid.values())

zone_list = ['QC-LCC', 'NB-NAD83(CSRS)', 'PEI-NAD83(CSRS)', 'AB-3TM-111', 'AB-3TM-114', 'AB-3TM-117', 'AB-3TM-120',
             'AB-UTM-111', 'AB-UTM-117', 'AB-10TM', 'BC-3TM-111', 'BC-3TM-114', 'BC-3TM-117', 'BC-3TM-120',
             'BC-3TM-123', 'BC-3TM-126', 'BC-3TM-129', 'BC-3TM-132', 'BC-3TM-135', 'BC-3TM-138', 'BC-3TM-141',
             'BC-6TM-111', 'BC-6TM-117', 'BC-6TM-123', 'BC-6TM-129', 'BC-6TM-135', 'BC-6TM-141', 'BC-10TM-115',
             'BC-10TM-125', 'BC-10TM-135', 'NL-1', 'NL-2', 'NL-3', 'NL-4', 'NL-5', 'NL-6', 'NS-NAD83-1997-4',
             'NS-NAD83-1997-5', 'NS-NAD83-2010-4', 'NS-NAD83-2010-5', 'ON-8', 'ON-9', 'ON-10', 'ON-11', 'ON-12',
             'ON-13', 'ON-14', 'ON-15', 'ON-16', 'ON-17', 'QC-2', 'QC-3', 'QC-4', 'QC-5', 'QC-6', 'QC-7', 'QC-8',
             'QC-9', 'QC-10', 'UTM1', 'UTM2', 'UTM3', 'UTM4', 'UTM5', 'UTM6', 'UTM7', 'UTM8', 'UTM9', 'UTM10', 'UTM11',
             'UTM12', 'UTM13', 'UTM14', 'UTM15', 'UTM16', 'UTM17', 'UTM18', 'UTM19', 'UTM20', 'UTM21', 'UTM22', 'UTM23',
             'UTM24', 'UTM25', 'UTM26', 'UTM27', 'UTM28', 'UTM29', 'UTM30', 'UTM31', 'UTM32', 'UTM33', 'UTM34', 'UTM35',
             'UTM36', 'UTM37', 'UTM38', 'UTM39', 'UTM40', 'UTM41', 'UTM42', 'UTM43', 'UTM44', 'UTM45', 'UTM46', 'UTM47',
             'UTM48', 'UTM49', 'UTM50', 'UTM51', 'UTM52', 'UTM53', 'UTM54', 'UTM55', 'UTM56', 'UTM57', 'UTM58', 'UTM59',
             'UTM60']

# Argument Parsing
parser = argparse.ArgumentParser(
    description='==================================== NRCan Geodetic Tools: NTv2 ====================================',
    epilog='====================================================================================================')

parser.add_argument('-g', '--grid', help=f'Grid (Default: NTV2) | See --grid_list for a list of options',
                    default='NTV2')
parser.add_argument('-x', help='Latitude or Easting')
parser.add_argument('-y', help='Longitude or Northing')
parser.add_argument('-oc', '--originCoord', help='Origin coordinate system | geo (Geographic), plan (Projection)',
                    choices=['geo', 'plan'], default='geo', type=str.lower)
parser.add_argument('-dc', '--destCoord', help='Destination coordinate system | geo (Geographic), plan (Projection)',
                    choices=['geo', 'plan'], default='geo', type=str.lower)
parser.add_argument('-oz', '--originZone', help='Zone for projection coordinates (ex. UTM1)')
parser.add_argument('-dz', '--destZone', help='Zone for projection coordinates (ex. UTM1)')
parser.add_argument('-wp', '--westpos', help='Turn West Positive false (Default: true)', choices=['true', 'false'],
                    default='true', type=str.lower)
parser.add_argument('-i', '--inverse',
                    help='Switch the "FROM" and "TO" reference systems. Depending on your selection of grid, '
                         'reference systems are between NAD27, ATS77, NAD83(Original), and NAD83(CSRS)',
                    choices=['on', 'off'], default='off', type=str.lower)
parser.add_argument('-gl', '--grid_list', help='List grids and their coverage', action='store_true')
# Batch Mode Specific
parser.add_argument('-f', '--file_path', help='File path of batch file (Default .csv format)', type=str)
parser.add_argument('-d', '--download_path', help='File path to download results', type=str)
args = parser.parse_args()


if args.grid_list:
    # Formatting Dictionary of Dictionaries for 'Grids', 'Coverage', 'From' reference frames and 'To' reference frames
    print(f"| {'Grid':<{max_grid_len}} | {'Coverage':^{max_coverage_len}} | {'From':^{max_from_len}} |"
          f" {'To':^{max_to_len}} ")

    print(
        f"|{'-' * (max_grid_len + 2)}|{'-' * (max_coverage_len + 2)}|{'-' * (max_from_len + 2)}|"
        f"{'-' * (max_to_len + 2)}|")

    for grid, data in coverage_and_grid.items():
        print(f"| {grid:<{max_grid_len}} | {data['Coverage']:<{max_coverage_len}} | {data['From']:<{max_from_len}} | "
              f"{data['To']:<{max_to_len}} |")

    exit()
elif not args.file_path and (args.grid and args.x and args.y and args.originCoord and args.destCoord) is None:
    sys.exit('ERROR: The following arguments are required to access NTv2; -g, -x, -y, -oc, -dc')
elif args.file_path and (args.grid and args.destCoord) is None:
    sys.exit('ERROR: The following arguments are required for Batch Processing [-f]: -g, -dc.')

x = args.x
y = args.y
ocoord = args.originCoord
dcoord = args.destCoord
westpos = args.westpos

# Special case (brackets will not pass through console)
if args.originZone is None:
    ozone = args.originZone  # Cannot .upper() NoneType
elif args.originZone.upper().startswith('NB'):
    ozone = 'NB-NAD83(CSRS)'
elif args.originZone.upper().startswith('PEI'):
    ozone = 'PEI-NAD83(CSRS)'
else:
    ozone = args.originZone.upper()

if args.destZone is None:
    dzone = args.destZone  # Cannot .upper() NoneType
elif args.destZone.upper().startswith('NB'):
    dzone = 'NB-NAD83(CSRS)'
elif args.destZone.upper().startswith('PEI'):
    dzone = 'PEI-NAD83(CSRS)'
else:
    dzone = args.destZone.upper()

if dzone is None and dcoord == 'plan':
    dzone = 'UTM'


# Check if inputs are valid
if ozone is not None:
    try:
        zone_list.index(ozone)
    except ValueError:
        sys.exit('Error: Inputted "Origin Zone" does not match any on record')

if dzone == 'UTM':
    pass
elif dzone is not None:
    try:
        zone_list.index(dzone)
    except ValueError:
        sys.exit('Error: Inputted "Destination Zone" does not match any on record')

# Checking if selected Grid is listed (Case insensitive)
grid = None
try:
    match = False
    for key in coverage_and_grid.keys():
        if args.grid.lower() == key.lower():
            grid = key
            match = True
            break
    if not match:
        raise ValueError('ERROR: Inputted "Grid" does not match any on record. Please use --grid_list to see options.')
except ValueError as e:
    sys.exit(e)

# Inverse Calculations
if args.inverse == 'on':
    mode = 'inverse'
else:
    mode = 'direct'

# <- Batch Mode Processing ->
if args.file_path:
    print('=> Batch Mode Processing')

    # URL and File Information
    domain = 'https://webapp.csrs-scrs.nrcan-rncan.gc.ca'
    url = domain + '/CSRS/tools/NTV2/upload'
    browser_name = 'NTv2 access via Python Browser Emulator'

    file_abspath = os.path.abspath(args.file_path)
    (file_path, input_file) = os.path.split(file_abspath)
    (csv_name, suffix) = os.path.splitext(input_file)

    try:
        os.chdir(file_path)
    except FileNotFoundError:
        sys.exit('ERROR: Cannot access directory {0:s}'.format(file_path))

    if input_file is None:
        sys.exit('ERROR: No .{0:s} file found.'.format(suffix))

    print('=> Batch File Information: {0:s}: {1:s} [{2:s}]'.format(suffix.upper(), input_file, file_path))

    # Batch Mode Content
    content = {
        'lang': 'en',
        'grid': grid,
        'destproj': dcoord,
        'destzone': dzone,
        'dir': mode,
        'file': (input_file, open(input_file, 'rb'), 'text/plain')
    }

    # Format Browser Content
    mtp_data = MultipartEncoder(fields=content)
    header = {'Content-Type': mtp_data.content_type}
    # Initialize Request
    req = requests.post(url, data=mtp_data, headers=header)
    print('=> Content Submitted')

    result_name = 'batch_ntv2_output{0:s}'.format(suffix)

    # Check if file name exists (replace)
    if os.path.isfile(result_name):
        os.remove(result_name)
    print('=> Get results file {0:s}'.format(result_name))

    # Write new file
    with open(result_name, 'wb') as f:
        f.write(req.content)
        print('=> Results downloaded [{0:s}]'.format(result_name))

    # Move content to desired path if download path specified (Default: Same Directory)
    if args.download_path:
        shutil.move(result_name, '{0}/{1}'.format(args.download_path, result_name))
        print('=> Results moved to {0}'.format(args.download_path))

    if suffix == '.zip':
        try:
            zip_ref = zipfile.ZipFile(result_name).testzip()
        except zipfile.BadZipFile as e:
            sys.exit('ERROR: Bad ZIP file')

    sys.exit('=> Batch Mode Processing: Completed')

# Sending to Web-Service
service_url = 'https://webapp.csrs-scrs.nrcan-rncan.gc.ca/CSRS/tools/NTV2/' + mode + '?'

url = service_url + urllib.parse.urlencode({'dataType': 'json',
                                            'lang': 'en',
                                            'proj': ocoord,
                                            'zone': ozone,
                                            'westpos': args.westpos,
                                            'x': x,
                                            'y': y,
                                            'grid': grid,
                                            'destproj': dcoord,
                                            'destzone': dzone})
print('Retrieving', url)


# Convert JSON to dict
try:
    results_dict = json.loads(urlopen(url).read().decode())
except json.JSONDecodeError:
    results_dict = None


# Print results
try:  # Check for Error
    error = results_dict['Errors']['Msg']
    x = True
except KeyError:
    error = 'None'
    x = False

if x is False:
    print('Results:')
    print(json.dumps(results_dict, indent=4))
elif x is True:
    print('ERROR:', error)

quit()  # Once completed application will quit


# -------------------------------------------------------------------------------------------------------------------- #
#                   Natural Resources Canada | Geodetic Tools: NTv2 | Last Updated: (2023-03-13)                       #
# -------------------------------------------------------------------------------------------------------------------- #
# Useful Links:                                                                                                        #
#       - https://webapp.geod.nrcan.gc.ca/geod/tools-outils/ntv2.php                                                   #
#         NTv2 Online Web-tool                                                                                         #
#       - https://www.nrcan.gc.ca/maps-tools-and-publications/geodetic-reference-systems/data/10923                    #
#         NRCan Geodetic Tools and Data                                                                                #
#                                                                                                                      #
# Script Flags:                                                                                                        #
#       - *[-g | --grid] For selecting Grid. Web-service uses Grid Shift Files (.GSB format)                           #
#       - *[-x | -destCoord] Latitude, X or Easting Parameter                                                          #
#       - *[-y] Longitude, Y or Northing Parameter                                                                     #
#       - *[-oc | -- originCoord] Origin Coordinate System (Options: geo OR plan)                                      #
#       - *[-dc | --destCoord] Destination Coordinate System (Options: geo OR plan)                                    #
#       - [-oz | --originZone] Origin Zone for Projection Coordinate System (Ex. UTM1)                                 #
#       - [-dz | --destZone] Destination Zone for Projection Coordinate System (Ex. UTM1)                              #
#       - [-wp | --westpos] Turn on/off Longitude West Positive. (Options: true, false) (Default: 'true')              #
#       - [-i | --inverse] Switches the 'From' and 'To' reference frames.                                              #
#       - [-gl | --grid_list] Displays all 'Grid' names, 'Coverages', 'From' and 'To' reference frames.                #
#       * Required argument for all types of calculations with NTv2                                                     #
#                                                                                                                      #
# Example Script Run and Responses:                                                                                    #
#     >>> python3.9 NTv2.py -g NA27SCRS -x 422567.817 -y 5094533.591 -oz UTM19 -oc plan -dc geo -i on                  #
#                                                                                                                      #
#     NTv2 Web-service Response:                                                                                       #
#           {"Transformed":{"Zone":"UTM19","X":"422530.604","Y":"5094310.558","Z":"0.000","Proj":"plan"},              #
#           "Shift":{"DXm":"-37.213","SigDXm":"0.000","DYm":"-223.033","SigDYm":"0.000"},                              #
#           "Zone":"UTM19","X":"422567.817","Y":"5094533.591","Z":"0.000","Proj":"plan"}                               #
#                                                                                                                      #
#                                                                                                                      #
#     >>> python3.9 NTv2.py -g NA27SCRS -x 46.0 -y 70.0 -oc geo -dc plan -dz UTM19                                     #
#                                                                                                                      #
#     NTv2 Web-service Response:                                                                                       #
#           {"Transformed": {"Zone": "UTM19", "X": "422602.683", "Y": "5094538.672", "Z": "0.000","Proj": "plan"},     #
#           "Shift": {"DXm": "37.202","SigDXm": "0.000","DYm": "223.038","SigDYm": "0.000"},                           #
#           "X": "46.0","Y": "70.0","Z": "0.000","Proj": "geo"}                                                        #
#                                                                                                                      #
#                                                                                                                      #
# API Arguments:                                                                                                       #
#       Query Variables:                                    Response Variables:                                        #
#         - lang                                              - proj                                                   #
#         - proj                                              - Shift {                                                #
#         - westpos                                                    - DXm  -SigDXm                                  #
#         - x                                                          - DYm  - SigDym }                               #
#         - y                                                 - Transformed {                                          #
#         - grid                                                       - Proj  - X                                     #
#         - zone                                                       - Y     - Z                                     #
#         - destzone                                                   - Zone }                                        #
#         - destproj                                          - X                                                      #
#                                                             - Y                                                      #
#                                                             - Z                                                      #
#                                                                                                                      #
# -------------------------------------------------------------------------------------------------------------------- #
#                                                                                                                      #
#     If you require further assistance please contact: geodeticinformation-informationgeodesique@nrcan-rncan.gc.ca    #
#                                                                                                                      #
# -------------------------------------------------------------------------------------------------------------------- #
