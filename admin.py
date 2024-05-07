#admin.py - information for admin settings
#  No spaces allowed on either side of equal sign, '='.
#  Version Format, i.e. v4.310
#    'v' must be present in the version description
#    version 4
#    subversion 3
#    minor update 1
#    error fix 0
#
# Off Admin Menu Items - features that haven't been included in the web admin page include;
#    Use 'use_mos'; 0 = No, 1 = Yes
#      For regions outside of the US, set this to 0 so it won't try to download data that's not usable for the region.
#    Multiple Home Airports (mult_homes)
#      Create a list of airport LED pin numbers, i.e. mult_homes=['170','172','173','176'] to highlight more than 1 home airport
#      Leave blank if only one airport is to be used as a home airport and fill this in the web interface. i.e. mult_homes=[]

version='v4.503'
map_name='LiveSectional'
min_update_ver='4.350'
use_mos=1
use_scan_network=0
use_reboot=0
time_reboot='01:00'
mult_homes=[]

