#!/usr/bin/env python

# -------------------------------------------------------------------------------------------------------------------- #
#            Use of Canadian Geodetic Survey products and data is subject to the Open Government Licence - Canada      #
#                                  https://open.canada.ca/en/open-government-licence-canada                            #
# -------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------------------------------- #
#                                                                                                                      #
#                                              NRCan Geodetic Tools and Data: INDIR                                    #
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


ellipsoid_dict = {
    0: 'GRS80',
    1: 'WGS84',
    2: 'Clarke 1866',
    3: 'ATS77',
    4: 'International',
    5: 'Bessel',
    6: 'Krassovsky',
    7: 'Everest',
    8: 'Clarke 1880',
    9: 'Australia National',
    10: 'Fisher (Mercury)',
    11: 'Fisher(Asia)',
    12: 'Hoygh',
    13: 'Average Terrestrial',
    14: 'NWL9D',
    15: 'NWL10F (WGS72)'
}

# Argument Parsing
parser = argparse.ArgumentParser(
    description='==================================== NRCan Geodetic Tools: NTv2 ====================================',
    epilog='====================================================================================================')

parser.add_argument('-e', '--ellipsoid', help=f'Ellipsoid (Default: "GRS80") [Enter values with quotes to pass through '
                    f'console] | See --ellipsoid_dict for a list of options', default='GRS80', type=str)
parser.add_argument('-x1', help='Latitude 1')
parser.add_argument('-y1', help='Longitude 1')
parser.add_argument('-z1', help='Ellipsoidal Height for 3D (-3d)')
parser.add_argument('-3d', '--three_dimension', help='3D mode to turn on "Heights" for geodetic inverse or direct'
                    ' computations (Default: false)', choices=['true', 'false'], default='false', type=str.lower)
parser.add_argument('-indir', help='Toggle the "Direct" or "Indirect" method. (Default: direct)',
                    choices=['direct', 'indirect'], default='direct', type=str.lower)
parser.add_argument('-x2', help='Distance [meters] (Direct) or Latitude 2 (Indirect)')
parser.add_argument('-y2', help='Forward Azimuth (Direct) or Longitude 2 (Indirect)')
parser.add_argument('-z2', help='Zenith (Direct) or Ellipsoidal Height 2 (Indirect) for 3D (-3d)')
parser.add_argument('-dh', '--delta_h', help='Delta h or change in ellipsoidal height can be used as an alternative'
                    ' to Zenith (-z2) for Direct method only')
parser.add_argument('-wp', '--westpos', help='Turn West Positive false (Default: true)', choices=['true', 'false'],
                    default='true', type=str.lower)
parser.add_argument('-el', '--ellipsoid_list', help='List all available ellipsoids', action='store_true')
# Batch Mode Specific
parser.add_argument('-f', '--file_path', help='File path of batch file (Default .csv format)', type=str)
parser.add_argument('-d', '--download_path', help='File path to download results', type=str)
args = parser.parse_args()


if args.ellipsoid_list:
    print('Ellipsoid List:')
    for ellipsoid in ellipsoid_dict.values():
        print(ellipsoid)
elif args.file_path and not (args.ellipsoid and args.three_dimension):
    sys.exit('ERROR: The following arguments are required for Batch Mode [-f]: -e, -3d')
elif not args.file_path and (args.x1 and args.y1 and args.x2 and args.y2 and args.ellipsoid) is None:
    sys.exit('ERROR: The following arguments are required for all usages of INDIR; -x1, -y1, -x2, -y2, -e')

# Argument Storing (Based on selections)
westpos = args.westpos

ellipsoid_key = None
if args.ellipsoid is not None:
    try:
        for key, ellipsoid in ellipsoid_dict.items():
            if args.ellipsoid.lower() == ellipsoid.lower():
                ellipsoid_key = key
                break
    except ValueError:
        print('ERROR: Inputted Ellipsoid does not match any on record.')
        print('Possible Inputs:')
        for ellipsoid in ellipsoid_dict.values():
            print(ellipsoid)
        sys.exit()

ellipsoid = ellipsoid_dict.get(ellipsoid_key)
if ellipsoid is None:
    print('ERROR: Inputted Ellipsoid does not match any on record.')
    print('Possible Inputs:')
    for ellipsoid in ellipsoid_dict.values():
        print(ellipsoid)
    sys.exit()

# <- Batch Mode Processing ->
if args.file_path:
    print('=> Batch Mode Processing')

    # URL and File Information
    domain = 'https://webapp.csrs-scrs.nrcan-rncan.gc.ca'
    url = domain + '/CSRS/tools/INDIR/upload'
    browser_name = 'INDIR access via Python Browser Emulator'

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

    # Warnings
    if args.three_dimension == 'false':
        print('WARN: For Batch Mode, 3D is default TRUE and you have it set to FALSE.')

    # Corrective Statements
    if args.three_dimension == 'true':
        three_d = 'on'
    else:
        three_d = 'off'

    # Batch Mode Content
    content = {
        'lang': 'en',
        'ellipsoid': ellipsoid,
        '3d': three_d,
        'file': (input_file, open(input_file, 'rb'), 'text/plain')
    }

    # Format Browser Content
    mtp_data = MultipartEncoder(fields=content)
    header = {'Content-Type': mtp_data.content_type}
    # Initialize Request
    req = requests.post(url, data=mtp_data, headers=header)
    print('=> Content Submitted')

    result_name = 'batch_indir_output{0:s}'.format(suffix)

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


x1 = args.x1
y1 = args.y1

z1 = ''
z2 = ''
if args.three_dimension == 'true':
    if args.z1 is not None:
        z1 = args.z1
    else:
        sys.exit('ERROR: For 3D usage, you must enter a valid first height (-z1).')

if args.indir == 'direct':
    distance = args.x2
    azimuth = args.y2
    x2 = ''
    y2 = ''
    if args.three_dimension == 'true':
        if args.z2 is not None:
            zenith = args.z2
        else:
            zenith = ''
        if args.delta_h is not None:
            dh = args.delta_h
        else:
            dh = ''
        if (args.delta_h or args.z2) is None:
            sys.exit('ERROR: For 3D usage (-3d) you must provide forward zenith (-z2) OR delta_H (-dh).')
    else:
        zenith = ''
        dh = ''
else:
    x2 = args.x2
    y2 = args.y2
    distance = ''
    azimuth = ''
    if args.three_dimension == 'true':
        z2 = args.z2
        zenith = ''
        dh = ''
        if args.z2 is None:
            sys.exit('ERROR: For 3D usage, a second height must be inputted (-z2).')
    else:
        zenith = ''
        dh = ''

# Point 2; Mode Selection
if args.indir == 'indirect':
    mode = 'inverse'
else:
    mode = 'direct'

# Unicode substitution
ellipsoid = ellipsoid.replace(' ', '%20').replace('(', '%28').replace(')', '%29')




# Sending to web service
service_url = 'https://webapp.csrs-scrs.nrcan-rncan.gc.ca/CSRS/tools/INDIR/' + mode + '/' + ellipsoid + '?'

url = service_url + urllib.parse.urlencode({'dataType': 'json',
                                            'lang': 'en',
                                            'westpos': westpos,
                                            'ellipsoid': ellipsoid,
                                            '3d': args.three_dimension,
                                            'x': x1,
                                            'y': y1,
                                            'z': z1,
                                            'dis': distance,
                                            'azi': azimuth,
                                            'zen': zenith,
                                            'dh': dh,
                                            'x2': x2,
                                            'y2': y2,
                                            'z2': z2})
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
#                   Natural Resources Canada | Geodetic Tools: INDIR | Last Updated: (2023-04-14)                      #
# -------------------------------------------------------------------------------------------------------------------- #
# Useful Links:                                                                                                        #
#       - https://webapp.geod.nrcan.gc.ca/geod/tools-outils/indir.php                                                  #
#         INDIR Online Web-tool                                                                                        #
#       - https://www.nrcan.gc.ca/maps-tools-and-publications/geodetic-reference-systems/data/10923                    #
#         NRCan Geodetic Tools and Data                                                                                #
#                                                                                                                      #
# Script Flags:                                                                                                        #
#       - *[-e | --ellipsoid] Selecting the Ellipsoid for INDIR usage.                                                 #
#       - *[-x1] Latitude 1.                                                                                           #
#       - *[-y1] Longitude 1.                                                                                          #
#       - [-z1] Ellipsoidal height for Three Dimension INDIR usage.                                                    #
#       - [-3d | --three_dimension] 3D mode to turn on "Heights" for geodetic inverse or direct computations.          #
#       - [-indir] Toggle the "Direct" or "Indirect" method.                                                           #
#       - *[-x2] Latitude 2.                                                                                           #
#       - *[-y2] Longitude 2.                                                                                          #
#       - [-z2] Zenith (Direct) or Ellipsoidal Height 2 (Indirect) for 3D calculations.                                #
#       - [-dh | --delta_h] Change in Ellipsoidal Height can be used as an alternative to Zenith (-z2) [Direct Only]   #
#       - [-wp | --westpos] (Options: true, false) Turn on/off Longitude West Positive. (Default: 'true')              #
#       - [-el | --ellipsoid_list] Displays all 'Ellipsoid' names.                                                     #
#       * Required argument for all types of calculations with INDIR                                                   #
#                                                                                                                      #
# Example Script Run and Responses:                                                                                    #
#     >>> python3.9 INDIR.py -e grs80 -x1 46 -y1 101 -z1 0 -x2 1000 -y2 2 -z2 1 -3d true                               #
#                                                                                                                      #
#     INDIR Web-service Response:                                                                                      #
#           {"Transformed":{"X":"46.00015689","Y":"100.99999214","Z":"999.848","Proj":"geo"},                          #
#           "DIS":"1000.000","AZI":"2.0","ZEN":"1.0","X":"46.0","Y":"101.0","Z":"0.000","Proj":"geo"}                  #
#                                                                                                                      #
#                                                                                                                      #
#     >>> python3.9 INDIR.py -e "Clarke 1866" -x1 53 -y1 120 -z1 181 -3d true -x2 57 -y2 150 -z2 180 -indir indirect   #
#                                                                                                                      #
#     INDIR Web-service Response:                                                                                      #
#           {"Transformed":{"ELLdis":"1953721.819","ELLfaz":"295.153","MTMzen":"98.7573","ELLbaz":"90.3787",           #
#           "MTMbaz":"90.3785","MTMdis":"1946180.852","MTMfaz":"295.1524","Proj":"geo"},"X2":"57.0","Y2":"150.0",      #
#           "Z2":"180.000","X":"53.0","Y":"120.0","Z":"181.000","Proj":"geo"}                                          #
#                                                                                                                      #
#                                                                                                                      #
# API Arguments:                                                                                                       #
#       Query Variables:                 Response Variables (Indirect):             Response Variables (Direct):       #                                       #
#         - lang            - dis           -  Proj                                     - Proj                         #
#         - 3d              - azi           - Transformed {                             - Transformed {                #
#         - westpos         - zen               - EllBaz    - Elldis                        - Proj      - X            #
#         - ellipsoid       - dh                - Ell faz   - MTMbaz                        - Y         - Z  }         #
#         - x               - x2                - MTMdis    - MTMfaz                    - AZI    - ZEN                 #
#         - y               - y2                - MTMzen    - Proj  }                   - DIS                          #
#         - z               - z2                - X    - X2                             - X                            #
#                                               - Y    - Y2                             - Y                            #
#                                               - Z    - Z2                             - Z                            #
#                                                                                                                      #
# -------------------------------------------------------------------------------------------------------------------- #
#                                                                                                                      #
#     If you require further assistance please contact: geodeticinformation-informationgeodesique@nrcan-rncan.gc.ca    #
#                                                                                                                      #
# -------------------------------------------------------------------------------------------------------------------- #
