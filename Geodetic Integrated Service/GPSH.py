#!/usr/bin/env python

# -------------------------------------------------------------------------------------------------------------------- #
#            Use of Canadian Geodetic Survey products and data is subject to the Open Government Licence - Canada      #
#                                  https://open.canada.ca/en/open-government-licence-canada                            #
# -------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------------------------------- #
#                                                                                                                      #
#                                             NRCan Geodetic Tools and Data: GPS-H                                     #
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
# __maintainer__ = 'Rye Godin'
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


# Reference Frame List (Future Versions to call web service)
rf_list = ['NAD83(CSRS)', 'ITRF2020', 'ITRF2014', 'ITRF2008', 'ITRF2005', 'ITRF2000', 'ITRF97', 'ITRF96', 'ITRF94',
           'ITRF93', 'ITRF92', 'ITRF91', 'ITRF90', 'ITRF89', 'ITRF88']

geoid_list = {
    0: 'CGG2013a',
    1: 'CGG2013',
    2: 'HT2_2010v70',
    3: 'HT2_2002v70',
    4: 'HT2_1997',
    5: 'CGG2010',
    6: 'CGG2005',
    7: 'CGG2000',
    8: 'GSD95',
    9: 'GSD91',
    10: 'EGM08'
}

# Zones for Projection Coordinates
zone_list = ['QC-LCC', 'NB-NAD83(CSRS)', 'PEI-NAD83(CSRS)', 'AB-3TM-111', 'AB-3TM-114', 'AB-3TM-117', 'AB-3TM-120',
             'AB-UTM-111', 'AB-UTM-117', 'AB-10TM', 'BC-3TM-111', 'BC-3TM-114', 'BC-3TM-117', 'BC-3TM-120',
             'BC-3TM-123',
             'BC-3TM-126', 'BC-3TM-129', 'BC-3TM-132', 'BC-3TM-135', 'BC-3TM-138', 'BC-3TM-141', 'BC-6TM-111',
             'BC-6TM-117', 'BC-6TM-123', 'BC-6TM-129', 'BC-6TM-135', 'BC-6TM-141', 'BC-10TM-115', 'BC-10TM-125',
             'BC-10TM-135', 'NL-1', 'NL-2', 'NL-3', 'NL-4', 'NL-5', 'NL-6', 'NS-NAD83-1997-4', 'NS-NAD83-1997-5',
             'NS-NAD83-2010-4', 'NS-NAD83-2010-5', 'ON-8', 'ON-9', 'ON-10', 'ON-11', 'ON-12', 'ON-13', 'ON-14', 'ON-15',
             'ON-16', 'ON-17', 'QC-2', 'QC-3', 'QC-4', 'QC-5', 'QC-6', 'QC-7', 'QC-8', 'QC-9', 'QC-10', 'UTM1', 'UTM2',
             'UTM3', 'UTM4', 'UTM5', 'UTM6', 'UTM7', 'UTM8', 'UTM9', 'UTM10', 'UTM11', 'UTM12', 'UTM13', 'UTM14',
             'UTM15', 'UTM16', 'UTM17', 'UTM18', 'UTM19', 'UTM20', 'UTM21', 'UTM22', 'UTM23', 'UTM24', 'UTM25', 'UTM26',
             'UTM27', 'UTM28', 'UTM29', 'UTM30', 'UTM31', 'UTM32', 'UTM33', 'UTM34', 'UTM35', 'UTM36', 'UTM37', 'UTM38',
             'UTM39', 'UTM40', 'UTM41', 'UTM42', 'UTM43', 'UTM44', 'UTM45', 'UTM46', 'UTM47', 'UTM48', 'UTM49', 'UTM50',
             'UTM51', 'UTM52', 'UTM53', 'UTM54', 'UTM55', 'UTM56', 'UTM57', 'UTM58', 'UTM59', 'UTM60']

# Dictionary of Conversions
conversions_dict = {
    0: 'HT2_2010_to_CGG2013a',
    1: 'CGG2013a_HT2_2010',
    2: 'HT2_2002_to_CGG2013a',
    3: 'CGG2013a_HT2_2002',
    4: 'HT2_1997_to_CGG2013a',
    5: 'CGG2013a_HT2_1997'
}

parser = argparse.ArgumentParser(
    description='==================================== NRCan Geodetic Tools: GPS-H ====================================',
    epilog='==========================================================================================================')

parser.add_argument('-x', help='Latitude, X or Easting')
parser.add_argument('-y', help='Longitude, Y or Northing')
parser.add_argument('-z', '--height', help='Ellipsoidal Height. Add --hmode for Orthometric Height')
parser.add_argument('-hm', '--hmode', help='Add to enter Orthometric Height', default='off', choices=['on', 'off'],
                    type=str.lower)
parser.add_argument('-zn', '--zone', help=f'Zone for Projection Coordinates (Ex. UTM1) | Possible Inputs: {zone_list}')
parser.add_argument('-g', '--geoid', help=f'Geoid Model (Default: CGG2013a) | Possible Inputs: {geoid_list}',
                    default='CGG2013a')
parser.add_argument('-e', '--epoch', help='Epoch (Default: 1997-01-01) (Format: YYYY-MM-DD)', default='1997-01-01')
parser.add_argument('-rf', '--ref_frame', help=f'Reference Frame (Default: NAD83(CSRS) | Possible Inputs: {rf_list}',
                    default='NAD83')
parser.add_argument('-p', '--proj', help='geo (Geographic), car (Cartesian), plan (Projection)',
                    choices=['geo', 'car', 'plan'], default='geo', type=str.lower)
parser.add_argument('-c', '--convert',
                    help=f'Converting Geoids (Requires: --hmode) | Possible Inputs: {conversions_dict}')
parser.add_argument('-wp', '--westpos', help='Turn West Positive FALSE (Default: true)', default='true',
                    choices=['true', 'false'], type=str.lower)
# Batch Mode Specific
parser.add_argument('-eg', '--est_gravity', help='Estimate Gravity Toggle | Default: off', default='off',
                    choices=['on', 'off'], type=str.lower)
parser.add_argument('-f', '--file_path', help='File path of batch file (Default .csv format)', type=str)
parser.add_argument('-d', '--download_path', help='File path to download results', type=str)

args = parser.parse_args()

if args.file_path and not (args.geoid and args.ref_frame and args.epoch):
    sys.exit('Error: For Batch Mode Processing [-f] the following arguments are required: --geoid, --ref_frame, --epoch. '
             'OR for converting: --convert, --ref_frame')

# Logic Checks
if args.convert is None:
    if args.epoch is None:
        sys.exit('Error: Please enter an epoch [-e EPOCH]')

if args.proj == 'plan':
    if args.zone is None:
        sys.exit('Error: Projection coordinates require a zone. Refer to --help')

if args.proj == 'car':
    if args.hmode is not None:
        sys.exit('You can only convert ellipsoidal heights to orthometric heights for Cartesian coordinates.')

# Conversion Logic Checks
if args.convert is not None:
    if args.hmode != 'on':
        print('WARN: You can only use orthometric heights in geoid conversion (--hmode). --hmode turned ON')
        args.hmode = 'on'

if args.convert is not None:
    if args.proj == 'car':
        sys.exit('Error: Cartesian Coordinates do not work with conversion calculations.')

if args.convert is None:
    if args.geoid is None:
        sys.exit('Error: A Geoid Model is required.')

# Check if VALID; Geoid Model, Reference Frame and Zone (Projection Coordinates)
geoid_key = None
if args.geoid is not None:
    try:
        for key, geoid in geoid_list.items():
            if args.geoid.lower() == geoid.lower():
                geoid_key = key
                break
    except ValueError:
        print(
            'Error: Inputted Geoid Model does not match any on record.')
        print('Possible Inputs:', geoid_list)
        sys.exit()

# Any input of NAD for Reference Frame (Before INDEX)
if args.ref_frame.upper().startswith('NAD'):
    input_frame = 'NAD83(CSRS)'
else:
    input_frame = args.ref_frame.upper()

try:
    rf_list.index(input_frame)
except ValueError:
    print('Error: Inputted Reference Frame does not match any on record.')
    print('Possible Inputs:', rf_list)
    sys.exit()

# Special case (brackets will not pass through console)
if args.zone is None:
    zone = ''  # Cannot .upper() NoneType
elif args.zone.upper().startswith('NB'):
    zone = 'NB-NAD83(CSRS)'
elif args.zone.upper().startswith('PEI'):
    zone = 'PEI-NAD83(CSRS)'
else:
    zone = args.zone.upper()

if args.zone is not None:
    try:
        zone_list.index(zone.upper())
    except ValueError:
        print('Error: Inputted Zone does not match any on record.')
        print('Possible Inputs:', zone_list)
        sys.exit()

convert_key = None
if args.convert is not None:
    try:
        for key, convert in conversions_dict.items():
            if args.convert.lower() == convert.lower():
                convert_key = key
                break
    except ValueError:
        print(
            'Error: Inputted Conversion Type does not match any on record.')
        print('Possible Inputs:', conversions_dict)
        sys.exit()

# Changes link if CONVERT is enabled.
if args.convert is not None:
    geoidArg = conversions_dict.get(convert_key)
else:
    geoidArg = geoid_list.get(geoid_key)


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


# Initial parameters
# If the submitted date matches the format (YYYY-MM-DD) or is within appropriate year span
if date_format(args.epoch):
    epoch = args.epoch
else:
    try:  # Check if the inputted variable is instead a float, then check if it is within range.
        epoch = float(args.epoch)
        x = True
    except ValueError:
        x = False
    if x:
        if 1980.0 <= float(args.epoch) <= 2050.0:
            epoch = args.epoch
        else:
            sys.exit(f'ERROR: {args.epoch} is not within the 1980-2050 epoch frame.')
    else:
        sys.exit(f'ERROR: {args.epoch} is not a valid format or date (Format: YYYY-MM-DD)')

if args.geoid.lower() == 'ht2_2010v70':
    epoch = '2010-01-01'
    print('WARN: HT2_2010v70 geoid model will automatically set the epoch to 2010-01-01 for standard usage.')
elif args.geoid.lower() == 'ht2_2002v70':
    epoch = '2002-01-01'
    print('WARN: HT2_2002v70 geoid model will automatically set the epoch to 2002-01-01 for standard usage.')
elif args.geoid.lower() == 'ht2_1997':
    epoch = '1997-01-01'
    print('WARN: HT2_1997 geoid model will automatically set the epoch to 1997-01-01 for standard usage.')

proj = args.proj.lower()
hmode = args.hmode
westpos = args.westpos.lower()
x = args.x
y = args.y
z = args.height

# Silencing unnecessary arguments by case
if args.convert is not None:
    conversion_model = args.convert
    epoch = ''
    conversion = 'on'
else:
    conversion_model = ''
    conversion = ''


# <- Batch Mode Processing ->
if args.file_path:
    print('=> Batch Mode Processing')

    # URL and File Information
    domain = 'https://webapp.csrs-scrs.nrcan-rncan.gc.ca'
    url = domain + '/CSRS/tools/GPSH/upload'
    browser_name = 'GPS-H access via Python Browser Emulator'

    file_abspath = os.path.abspath(args.file_path)
    (file_path, input_file) = os.path.split(file_abspath)
    (csv_name, suffix) = os.path.splitext(input_file)

    try:
        os.chdir(file_path)
    except FileNotFoundError:
        sys.exit('ERROR: Cannot access directory {0:s}'.format(file_path))

    if input_file is None:
        sys.exit('ERROR: No .{0:s} file found.'.format(suffix))

    if args.est_gravity == 'on':
        grav = args.est_gravity
    else:
        grav = ''

    if geoidArg.lower().startswith('cgg2013'):
        v_datum = 'CGVD2013'
    elif geoidArg.lower().startswith('ht2'):
        v_datum = 'CGVD28'
    else:
        v_datum = 'Others'

    print('=> Batch File Information: {0:s}: {1:s} [{2:s}]'.format(suffix.upper(), input_file, file_path))

    # Batch Mode Content
    content = {
        'lang': 'en',
        'conversionModel': conversion_model,
        'batchdestdatum': v_datum,
        'geoidModel': geoidArg,
        'model': geoidArg,
        'frame': input_frame,
        'epoch': epoch,
        'grav': grav,
        'conversion': conversion,
        'file': (input_file, open(input_file, 'rb'), 'text/plain')
    }

    # Format Browser Content
    mtp_data = MultipartEncoder(fields=content)
    header = {'Content-Type': mtp_data.content_type}
    # Initialize Request
    req = requests.post(url, data=mtp_data, headers=header)
    print('=> Content Submitted')

    result_name = 'batch_gpsh_output{0:s}'.format(suffix)

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

# Service URL to NRCan software
service_url = 'https://webapp.csrs-scrs.nrcan-rncan.gc.ca/CSRS/tools/GPSH/' + geoidArg + '?'

# Data Call: Grabs information from URL
url = service_url + urllib.parse.urlencode({'dataType': 'json',
                                            'lang': 'en',
                                            'epoch': epoch,
                                            'frame': input_frame,
                                            'proj': proj,
                                            'x': x,
                                            'y': y,
                                            'z': z,
                                            'zone': zone,
                                            'westpos': westpos,
                                            'hmode': hmode,
                                            'conversion': conversion})
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

sys.exit()  # Once completed application will quit

# -------------------------------------------------------------------------------------------------------------------- #
#                   Natural Resources Canada | Geodetic Tools: GPS-H | Last Updated: (2023-02-03)                      #
# -------------------------------------------------------------------------------------------------------------------- #
# Useful Links:                                                                                                        #
#                                                                                                                      #
#       - https://webapp.csrs-scrs.nrcan-rncan.gc.ca/geod/tools-outils/gpsh.php?locale=en                              #
#         GPS-H Online Webtool                                                                                         #
#       - https://www.nrcan.gc.ca/maps-tools-and-publications/geodetic-reference-systems/data/10923                    #
#         NRCan Geodetic Tools and Data                                                                                #
#                                                                                                                      #
#                                                                                                                      #
# Script Flags:                                                                                                        #
#                                                                                                                      #
#       - [-h | --help] Shows all available flags and their meaning.                                                   #
#       - *[-p | --proj] (Options: geo, car, plan) Coordinate system of choice (Geographic, Cartesian, Projection)     #
#       - *[-x] Latitude, X or Easting Parameter                                                                       #
#       - *[-y] Longitude, Y or Northing Parameter                                                                     #
#       - *[-z | --height] The Ellipsoidal height or z level. (-hm | --hmode for Orthometric height)                   #
#       - [-hm | --hmode] (Options: on, off) Change the height to Orthometric value and outputs Ellipsoidal.           #
#                         (Default: 'off')                                                                             #
#       - [-zn | --zone] Zone for projection coordinate system. Refer to list at top of script for options.            #
#       - [-g | --geoid] Set the Geoid Model. Refer to list at top of script for options.                              #
#       - [-e | --epoch] Desired Epoch for calculation (Format: YYYY-MM-DD)                                            #
#       - *[-rf | --ref_frame] Desired reference system for calculation. Refer to list at top of script for options.    #
#       - [-wp | --westpos] (Options: true, false) Turn on/off Longitude West Positive. (Default: 'true')              #
#       - [-c | --convert] Conversion of Orthometric heights between vertical datums.                                  #
#                          Refer to list a top of script for options.                                                  #
#       * Required argument for all types of calculations with GPS-H.                                                  #
#                                                                                                                      #
#                                       Required for Height Conversion:                                                #
#                                       --> [-p] [-x] [-y] [-z] [-g] [-e] [-rs]                                        #
#                                                                                                                      #
#                                       Required for Geoid Conversion:                                                 #
#                                       --> [-p] [-x] [-y] [-z] [-c] [-hm on] [-rs]                                    #
#                                                                                                                      #
#                                                                                                                      #
# Example Script Runs and Responses:                                                                                   #
#                                                                                                                      #
#       >>> python3.9 GPSH.py -p geo -x 60 -y 60 -z 105.4 -hm on --geoid CGG2013a --epoch 2010-01-01 -rf ITRF2014      #
#           -wp true                                                                                                   #
#                                                                                                                      #
#  {"Epoch":"2011.0","Frame":"ITRF2014","Proj":"geo","X":"60.0","Y":"60.0","Z":"105.400","Gravity":"981883.7 ± 1.3",   #
#  "H_DYN":"100.529","HE":"105.400","HO":"100.399","N":"5.001","SigN":"0.012","westPos":"TRUE","VN":"1.280",           #
#  "DZ":"0.001","Xi":"-0.701","Eta":"-6.376"}                                                                          #
#                                                                                                                      #
#   Explanation: Using Geographic coordinates at 60 Latitude & 60 Longitude (WEST POSITIVE), converting Orthometric    #
#                height from 2010-01-01 to the Ellipsoidal height (-hm on) in the CGG2013a geoid model and ITRF2014    #
#                reference frame.                                                                                      #
#                                                                                                                      #
#                                                                                                                      #
#       >>> python3.9 GPSH.py -p geo -x 60.0 -y 101 -z 181.0 -wp true -hm on --convert HT2_2010_to_CGG2013a -rf NAD83  #
#                                                                                                                      #
#        {"Epoch":"2010.0","Frame":"NAD83(CSRS)","Proj":"geo","X":"60.0","Y":"101.0","Z":"181.000","HE":"181.000",     #
#        "HO":"180.958","Hmode":"on","N":"-0.042","westPos":"TRUE","VN":"0.000","DZ":"0.000"}                          #
#                                                                                                                      #
#   Explanation: Converting orthometric heights between two vertical datums (CGVD28(HT2_0) to CGVD2013(CGG2013a))      #
#                 at 60.0 Latitude & 101.0 Longitude (WEST POSITIVE) in the NAD83 reference frame.                     #
#                                                                                                                      #
#                                                                                                                      #
# API Arguments:                                                                                                       #
#                                                                                                                      #
#                   Query String Parameters:                                                                           #
#                       Geoid Conversions:                       Height Conversion:                                    #
#                          - lang                                  - lang                                              #
#                          - proj                                  - proj                                              #
#                          - conversion                            - hmode                                             #
#                          - westpos                               - westpos                                           #
#                          - conversionModel                       - destdatum                                         #
#                          - destdatum                             - geoidModel                                        #
#                          - geoidModel                            - model                                             #
#                          - model                                 - frame                                             #
#                          - frame                                 - epoch                                             #
#                          - x, y and z                            - x, y and z                                        #
#                          - Zone                                  - Zone                                              #
#                                                                                                                      #
#                   Response Variables:                                                                                #
#                      Geoid Conversions:                       Height Conversion:                                     #
#                          - Frame:                                - Epoch:        - SigN:                             #
#                          - HE:                                   - Frame:        - X:                                #
#                          - HO:                                   - Gravity:      - Y:                                #
#                          - N:                                    - HE:           - Z:                                #
#                          - Proj:                                 - HO:           - Zone:                             #
#                          - X:                                    - H_DYN:        - Combined:                         #
#                          - Y:                                    - Hmode:        - Convergence:                      #
#                          - Z:                                    - N:            - Scale:                            #
#                          - westPos:                              - Proj:         - westPos:                          #
#                          - Xi:                                   - Xi:           - Eta:                              #
#                          - Eta:                                                                                      #
#                                                                                                                      #
# -------------------------------------------------------------------------------------------------------------------- #
#                                                                                                                      #
#   If you require further assistance please contact: GeodeticInformation-InformationGeodesique@NRCan-RNCan.gc.ca      #
#                                                                                                                      #
# -------------------------------------------------------------------------------------------------------------------- #
