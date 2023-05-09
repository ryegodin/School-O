#!/usr/bin/env python

# -------------------------------------------------------------------------------------------------------------------- #
#            Use of Canadian Geodetic Survey products and data is subject to the Open Government Licence - Canada      #
#                                  https://open.canada.ca/en/open-government-licence-canada                            #
# -------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------------------------------- #
#                                                                                                                      #
#                                             NRCan Geodetic Tools and Data: TRX                                       #
#                                       For more information refer to the bottom of script                             #
#                                            Recommended Compatibility: Python 3.5+                                    #
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
from datetime import date
import re
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

# Reference Frame List (Future Versions to call webservice)
rf_list = ['NAD83(CSRS)', 'ITRF2020', 'ITRF2014', 'ITRF2008', 'ITRF2005', 'ITRF2000', 'ITRF97', 'ITRF96', 'ITRF94',
           'ITRF93', 'ITRF92', 'ITRF91', 'ITRF90', 'ITRF89', 'ITRF88']

# Zones for Projection Coordinates
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

parser = argparse.ArgumentParser(
    description='======================= NRCan Geodetic Tools: TRX ==========================',
    epilog='=============================================================================')

parser.add_argument('-x', help='Latitude, X, or Easting')
parser.add_argument('-y', help='Longitude, Y, or Northing')
parser.add_argument('-z', '--height', help='Ellipsoidal Height | Default: "0.0"', default='0.0')
parser.add_argument('-of', '--originRefFrame', help='Origin Reference Frame (Default: NAD83(CSRS)', default='NAD83')
parser.add_argument('-df', '--destRefFrame', help='Destination Reference Frame (Default: NAD83(CSRS)', default='NAD83')
parser.add_argument('-oe', '--originEpoch', help='Origin Epoch (Default: 2010-01-01)', default='2010-01-01')
parser.add_argument('-de', '--destEpoch', help='Destination Epoch (Format: YYYY-MM-DD)')
parser.add_argument('-oc', '--originCoord',
                    help='Origin Coordinate System: geo[*] (Geographic), car (Cartesian), plan (Projection)',
                    choices=['geo', 'car', 'plan'], default='geo', type=str.lower)
parser.add_argument('-dc', '--destCoord',
                    help='Destination Coordinate System: geo[*] (Geographic), car (Cartesian), plan (Projection)',
                    choices=['geo', 'car', 'plan'], default='geo', type=str.lower)
parser.add_argument('-oz', '--originZone', help='Zone for projection coordinates (ex. UTM14)')
parser.add_argument('-dz', '--destZone', help='Zone for projection coordinates (ex. UTM14)')
parser.add_argument('-vx', '--velocityX',
                    help='Enter your own velocity (default value from NAD83(CSRS) v7 velocity grid)')
parser.add_argument('-vy', '--velocityY',
                    help='Enter your own velocity (default value from NAD83(CSRS) v7 velocity grid)')
parser.add_argument('-vz', '--velocityZ',
                    help='Enter your own velocity (default value from NAD83(CSRS) v7 velocity grid)')
parser.add_argument('-et', '--epoch_trans', help='Toggle Epoch Transformation (Default: off)', choices=['on', 'off'],
                    default='off', type=str.lower)
parser.add_argument('-wp', '--westPos', help='Turn Longitude West Positive "false" (Default: true)',
                    choices=['true', 'false'], default='true', type=str.lower)
# Batch Mode Specific
parser.add_argument('-f', '--file_path', help='File path of batch file (Default .csv format)', type=str)
parser.add_argument('-d', '--download_path', help='File path to download results', type=str)
args = parser.parse_args()

if args.file_path and not (args.epoch_trans and args.originEpoch and args.originRefFrame and args.destRefFrame
                           and args.destCoord):
    sys.exit('ERROR: The following arguments are required for Batch Mode [-f]: -oe, -of, -df, -dc.')
elif not args.file_path and (args.x or args.y) is None:
    sys.exit('ERROR: The following arguments are required for TRX Single Calculations: -x, -y.'
             ' Others are required but have defaults for standard usage.')


# Function to check if submitted date matches required format
def date_format(epoch_string):
    # Find Regular Expression to Match
    format_d = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')
    match = format_d.match(epoch_string)
    if match:
        year, month, day = [int(g) for g in match.groups()]
        try:
            date(year, month, day)
        except ValueError:
            return False
        return True
    return False


ocoord = args.originCoord.lower()
x_input = args.x
y_input = args.y
z_input = args.height
vx = args.velocityX
vy = args.velocityY
vz = args.velocityZ

if args.destEpoch is not None and args.epoch_trans == 'off':
    sys.exit('ERROR: You entered a destination epoch while --epoch_trans was "off" (To turn on: -et on)')

# If the submitted date matches the format (YYYY-MM-DD) or is within appropriate year span
if date_format(args.originEpoch):
    oepoch = args.originEpoch
else:
    # Check if the inputted variable is instead a float, then check if it is within range
    try:
        oepoch = float(args.originEpoch)
        x = True
    except ValueError:
        x = False
    if x:
        if 1980.0 <= float(args.originEpoch) <= 2050.0:
            oepoch = args.originEpoch
        else:
            sys.exit(f'ERROR: {args.originEpoch} is not within the 1980-2050 epoch frame.')
    else:
        sys.exit(f'ERROR: {args.originEpoch} is not a valid format or date (Format: YYYY-MM-DD)')

if args.destEpoch is None:
    # If epochTrans is on but no destEpoch was entered: destEpoch = originEpoch
    depoch = ''
elif date_format(args.destEpoch):
    depoch = args.destEpoch
else:
    try:
        depoch = float(args.destEpoch)
        x = True
    except ValueError:
        x = False
    if x:
        if 1980.0 <= float(args.destEpoch) <= 2050.0:
            depoch = args.destEpoch
        else:
            sys.exit(f'ERROR: {args.destEpoch} is not within the 1980-2050 epoch frame.')
    else:
        sys.exit(f'ERROR: {args.destEpoch} is not a valid format or date (Format: YYYY-MM-DD)')

# Any input of NAD for NAD83 through console
if args.originRefFrame.upper().startswith('NAD'):
    orefframe = 'NAD83(CSRS)'
else:
    orefframe = args.originRefFrame.upper()

if args.destRefFrame.upper().startswith('NAD'):
    drefframe = 'NAD83(CSRS)'
else:
    drefframe = args.destRefFrame.upper()

epoch_trans = args.epoch_trans.lower()
dcoord = args.destCoord
westpos = args.westPos

# Special case (brackets will not pass through console)
if args.originZone is None:
    ozone = args.originZone  # Cannot .upper() NoneType
elif args.originZone.upper().startswith('NB'):
    ozone = 'NB-NAD83(CSRS)'
elif args.originZone.upper().startswith('PEI'):
    ozone = 'PEI-NAD83(CSRS)'
else:
    ozone = args.originZone.upper()

# Automatically choose correct zone
if ozone is None and ocoord == 'plan':
    ozone = ''

if args.destZone is None:
    dzone = args.destZone  # Cannot .upper() NoneType
elif args.destZone.upper().startswith('NB'):
    dzone = 'NB-NAD83(CSRS)'
elif args.destZone.upper().startswith('PEI'):
    dzone = 'PEI-NAD83(CSRS)'
else:
    dzone = args.destZone.upper()

if dzone is None and dcoord == 'plan':
    dzone = ''

# Require all velocities to be inputted if one is inputted
if vx is None:
    if vy or vz is not None:
        print('Please enter all velocities OR none if you want to use Interpolated Velocities')
        exit()
elif vy is None:
    if vx or vz is not None:
        print('Please enter all velocities OR none if you want to use Interpolated Velocities')
        exit()
elif vz is None:
    if vx or vy is not None:
        print('Please enter all velocities OR none if you want to use Interpolated Velocities')
        exit()

# If velocities are entered, do not interpolate velocities
if vx and vy and vz is not None:
    geovinterp = 'off'
    carvinterp = 'off'
    planvinterp = 'off'
else:
    geovinterp = 'on'
    carvinterp = 'on'
    planvinterp = 'on'

# Errors
try:
    rf_list.index(orefframe)
except ValueError:
    sys.exit('Error: Inputted Origin Reference Frame does not match any on record')

try:
    rf_list.index(drefframe)
except ValueError:
    sys.exit('Error: Inputted Destination Reference Frame does not match any on record')

if epoch_trans == 'on':
    if depoch is None:
        sys.exit('Error: You must input a destination epoch (-de | --destEpoch) for epoch transformations')

if ocoord == 'plan':
    if ozone is None:
        sys.exit('Error: You must enter a Origin Zone for a Projection Coordinate System')
if dcoord == 'plan':
    if dzone is None:
        dzone = ''  # Web service will pick the appropriate zone for coordinates

# Check if inputs are valid
if ozone is not None:
    try:
        zone_list.index(ozone)
    except ValueError:
        sys.exit('Error: Inputted "Origin Zone" does not match any on record')

if dzone == '':
    pass
elif dzone is not None:
    try:
        zone_list.index(dzone)
    except ValueError:
        sys.exit('Error: Inputted "Destination Zone" does not match any on record')

try:
    rf_list.index(orefframe)
except ValueError:
    sys.exit('Error: Inputted "Origin Reference Frame" does not match any on record')

try:
    rf_list.index(drefframe)
except ValueError:
    sys.exit('Error: Inputted "Destination Reference Frame" does not match any on record')

# <- Batch Mode Processing ->
if args.file_path:
    print('=> Batch Mode Processing')

    # URL and File Information
    domain = 'https://webapp.csrs-scrs.nrcan-rncan.gc.ca'
    url = domain + '/CSRS/tools/TRX/upload'
    browser_name = 'TRX access via Python Browser Emulator'

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

    content = {
        'lang': 'en',
        'epochTrans': epoch_trans,
        'frame': orefframe,
        'epoch': oepoch,
        'destframe': drefframe,
        'destproj': dcoord,
        'destepoch': depoch,
        'file': (input_file, open(input_file, 'rb'), 'text/plain')
    }
    # Batch Mode Content

    # Format Browser Content
    mtp_data = MultipartEncoder(fields=content)
    header = {'Content-Type': mtp_data.content_type}
    # Initialize Request
    req = requests.post(url, data=mtp_data, headers=header)
    print('=> Content Submitted')

    result_name = 'batch_trx_output{0:s}'.format(suffix)

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

# Get interpolated velocities from v7 velocity grid
if epoch_trans == 'on' and (geovinterp or carvinterp or planvinterp) == 'on':
    # NRCan Geodetic Tools, TRX velocity interpolation
    service_url_getVelocity = 'https://webapp.csrs-scrs.nrcan-rncan.gc.ca/CSRS/tools/TRX/vel/' + ocoord + '?'

    url_vel = service_url_getVelocity + urllib.parse.urlencode({'dataType': 'json',
                                                                'epoch': oepoch,
                                                                'destepoch': depoch,
                                                                'frame': orefframe,
                                                                'x': x_input,
                                                                'y': y_input,
                                                                'z': z_input,
                                                                'destframe': drefframe,
                                                                'destproj': dcoord,
                                                                'westpos': westpos})
    print('Retrieving', url_vel)

    # Convert JSON to dict
    try:
        resultsVel_dict = json.loads(urlopen(url_vel).read().decode())
    except json.JSONDecodeError:
        resultsVel_dict = None

    print(resultsVel_dict)

    # Set vx/vy/vz to interpolated values
    vx = resultsVel_dict['VX']
    vy = resultsVel_dict['VY']
    vz = resultsVel_dict['VZ']

# NRCan Geodetic Tools, TRX calculation
service_url = 'https://webapp.csrs-scrs.nrcan-rncan.gc.ca/CSRS/tools/TRX/calc/' + ocoord + '?'

# Generate URL
url = service_url + urllib.parse.urlencode({'dataType': 'json',
                                            'westpos': westpos,
                                            'epoch_trans': epoch_trans,
                                            'frame': orefframe,
                                            'epoch': oepoch,
                                            'x': x_input,
                                            'y': y_input,
                                            'z': z_input,
                                            'zone': ozone,
                                            'geovinterp': geovinterp,
                                            'vx': vx,
                                            'vy': vy,
                                            'vz': vz,
                                            'carvinterp': carvinterp,
                                            'planvinterp': planvinterp,
                                            'destframe': drefframe,
                                            'destproj': dcoord,
                                            'destzone': dzone,
                                            'destepoch': depoch})
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

if not x:
    print('Results:')
    print(json.dumps(results_dict, indent=4))
elif x:
    print('ERROR:', error)

quit()

# -------------------------------------------------------------------------------------------------------------------- #
#                   Natural Resources Canada | Geodetic Tools: TRX | Last Updated: (2023-01-09)                        #
# -------------------------------------------------------------------------------------------------------------------- #
# Useful Links:                                                                                                        #
#       - https://webapp.csrs-scrs.nrcan-rncan.gc.ca/geod/tools-outils/trx.php                                         #
#         TRX Online Web-tool                                                                                          #
#       - https://www.nrcan.gc.ca/maps-tools-and-publications/geodetic-reference-systems/data/10923                    #
#         NRCan Geodetic Tools and Data                                                                                #
#                                                                                                                      #
# Script Flags:                                                                                                        #
#       - *[-oc | -originCoord] Origin Coordinate System (Options: geo, car, plan)                                     #
#       - *[-dc | -destCoord] Destination Coordinate System (Options: geo, car, plan)                                  #
#       - *[-x] Latitude, X or Easting Parameter                                                                       #
#       - *[-y] Longitude, Y or Northing Parameter                                                                     #
#       - *[-z | --height] The ellipsoidal height or z level.                                                          #
#       - [-vx | --velocityX] Parameter for entering your own X velocity (Default from NAD83[CSRS] v7 Velocity Grid)   #
#       - [-vy | --velocityY] Parameter for entering your own Y velocity (Default from NAD83[CSRS] v7 Velocity Grid)   #
#       - [-vz | --velocityZ] Parameter for entering your own Z velocity (Default from NAD83[CSRS] v7 Velocity Grid)   #
#       - [-ozn | --originZone] Origin Zone for Projection Coordinate System (Ex. UTM1)                                #
#       - [-dzn | --destZone] Destination Zone for Projection Coordinate System (Ex. UTM1)                             #
#       - *[-oe | --originEpoch] Origin epoch of coordinates. (Format: YYYY-MM-DD)                                     #
#       - [-de | --destEpoch] Destination epoch for epoch transformations (Format: YYYY-MM-DD)                         #
#       - *[-of | --originRefFrame] Origin Reference Frame                                                             #
#       - *[-df | --destRefFrame] Destination Reference Frame                                                          #
#       - [-wp | --westPos] Turn on/off Longitude West Positive. (Options: true, false) (Default: 'true')              #
#       * Required argument for all types of calculations with TRX                                                     #
#                                                                                                                      #
# Example Script Run and Responses:                                                                                    #
#     >>> python3.9 TRX.py -oc geo -dc plan -x 46.0 -y 101.0 -z 181.0 -dz UTM14 -oe 2013-01-01 -de 2010-01-01          #
#         -of ITRF2020 -df ITRF2014 -et on                                                                             #
#                                                                                                                      #
#     NAD83[CSRS] v7 Velocity Grid Response:                                                                           #
#             {"X":"46.0","Y":"101.0","Z":"181.000","VX":"-5.09","VY":"-15.65","VZ":"-3.05","Epoch":"2013.0",          #
#             "Frame":"ITRF2020","Proj":"geo"}                                                                         #
#                                                                                                                      #
#     TRX Calculation Response:                                                                                        #
#             {"Transformed":{"Zone":"UTM14","X":"345136.473","Y":"5095992.185","Z":"181.007","Scale":"0.99989483",    #
#             "Combined":"0.99986646","Convergence":"1.439","VX":"-5.02","VY":"-15.63","VZ":"-2.84","Epoch":"2010.0",  #
#             "Frame":"ITRF2014","Proj":"plan"},"TRXepoch":"0.0","TX":"-0.0014","TY":"-0.0007","TZ":"0.0010",          #
#             "RX":"0.000","RY":"0.000","RZ":"0.000","DS":"-0.420","X":"46.0","Y":"101.0","Z":"181.000","VX":"-5.09",  #
#             "VY":"-15.65","VZ":"-3.05","Epoch":"2013.0","Frame":"ITRF2020","Proj":"geo"}                             #
#                                                                                                                      #
#     Explanation: Transforming geographic coordinates in the ITRF2020 reference frame to projection coordinates in    #
#                  the ITRF2014 reference frame. With an epoch transformation from 2013.0 to 2010.0.                   #
#                                                                                                                      #
# API Arguments:                                                                                                       #
#   Query Variables:                                    Response Variables:                                            #
#       - lang                  - vy                        - DS                - X                                    #
#       - epoch_trans           - vz                        - Epoch             - Y                                    #
#       - westpos               - geovinterp                - Frame             - Z                                    #
#       - frame                 - carvinterp                - Proj              - VX                                   #
#       - epoch                 - planvinterp               - RX                - VY                                   #
#       - x                     - destframe                 - RY                - VZ                                   #
#       - y                     - destproj                  - RZ                - Transformed:                         #
#       - z                     - destzone                  - TRXepoch              - Epoch         - Y                #
#       - vx                    - destepoch                 - TX                    - Proj          - Z                #
#                                                           - TY                    - VX            - Combined         #
#                                                           - TZ                    - VY            - Convergence      #
#                                                                                   - VZ            - Scale            #
#                                                                                   - X             - Zone             #
#                                                                                                                      #
# -------------------------------------------------------------------------------------------------------------------- #
#                                                                                                                      #
#     If you require further assistance please contact: geodeticinformation-informationgeodesique@nrcan-rncan.gc.ca    #
#                                                                                                                      #
# -------------------------------------------------------------------------------------------------------------------- #
