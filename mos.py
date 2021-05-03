# MOS decode routine
# MOS data is downloaded daily from; https://www.weather.gov/mdl/mos_gfsmos_mav to the local drive by crontab scheduling.
# Then this routine can be called to read through the entire file looking for those airports that are in the airports file. 
# If airport is found, the data is populated into a dictionary with the following format and then returned:
#  {
#    "AirportID": {
#      "YYYYMMDDHH": {
#        "Category1": "Value",
#        "Category2": "Value"
#        etc etc
#      }
#    }
#  }

# See; https://www.weather.gov/mdl/mos_gfsmos_mavcard 
# for a breakdown of what the MOS data looks like and what each line represents.

import re
from re import finditer

def parse(mos_file,airports):
    #Read current MOS text file
    try:
        file = open(mos_file, 'r')
        lines = file.readlines()
    except IOError as error:
        logger.error('MOS data file could not be loaded.')
        logger.error(error)
        return
    mos_data = {}
    station = ""
    year = ""
    hours = [] 
    date_dict = {}
    month_dict = {
        "JAN": "01",
        "FEB": "02",
        "MAR": "03",
        "APR": "04",
        "MAY": "05",
        "JUNE": "06",
        "JULY": "07",
        "AUG": "08",
        "SEP": "09",
        "OCT": "10",
        "NOV": "11",
        "DEC": "12"
    }
    year = ""
    collect = 0
    for line in lines:
        line = line.strip()
       
        if " GFS MOS GUIDANCE" in line:
            # Get station ID   
            station,year = re.findall('^(\w*)\s*GFS MOS GUIDANCE\s*\d+/\d+.(\d{4})\s*\d*', line)[0]
            # If this is a station we are looking for, process it
            if station in airports:
                mos_data[station] = {}
                collect = 1
            else:
                collect = 0
            continue
        
        if not collect:
            # This line does not need processed because it is not part
            # of a station we are looking for
            continue 
        if "DT /" in line:
            #Get the Month/Days
            one,two,three = re.findall('/(JAN|FEB|MAR|APR|MAY|JUNE|JULY|AUG|SEP|OCT|NOV|DEC)\s*(\d+)', line)
            
            # Remove the first 5 characters of the line so we can find location where two and three start
            # Knowing their location we can determine the date on each column of data
            s_line = line[5:]
            # Find location of the 2nd and third date
            l_two, l_three = finditer('/(JAN|FEB|MAR|APR|MAY|JUNE|JULY|AUG|SEP|OCT|NOV|DEC)\s*(\d+)', s_line)
            
            # Itterate over each column index so we can populate the date/hour for that column
            for i in range(21):
                if i == 0 :
                    # This first column is always the first date found in the line
                    date_dict[i] = year + month_dict[one[0]] + one[1].rjust(2,'0')
                    continue #Done with this column
                if ( i < ( l_two.span()[0] / 3) ):
                    # Until we get to the 2nd date, this column is for the first date
                    date_dict[i] = year + month_dict[one[0]] + one[1].rjust(2,'0')
                    continue #Done with this column
                if ( i >= ( l_two.span()[0] / 3) ) and ( i < ( l_three.span()[0] / 3 )):
                    # This column is for the 2nd date
                    # If this date is Jan 1st, then the year we parsed earlier is for the previous year
                    # If needed increment the year for this date
                    if ( month_dict[two[0]] == 'JAN' ) and ( two[1].rjust(2,'0') == '01'):
                        date_dict[i] = str(int(year) + 1 ) + month_dict[two[0]] + two[1].rjust(2,'0')
                    else:
                        date_dict[i] = year + month_dict[two[0]] + two[1].rjust(2,'0')
                    continue #Done with this column
                if ( i >= (l_three.span()[0] /3)):
                    # This column is for the 3rd date
                    # If this date is Jan 1st, then the year we parsed earlier is for the previous year
                    # If needed increment the year for this date
                    if ( ( ( month_dict[two[0]] == 'JAN' ) and ( two[1].rjust(2,'0') == '01')) or 
                         ( ( month_dict[three[0]] == 'JAN' ) and ( three[1].rjust(2,'0') == '01'))):
                        date_dict[i] = str(int(year) + 1 ) + month_dict[three[0]] + three[1].rjust(2,'0')
                    else:
                        date_dict[i] = year + month_dict[three[0]] + three[1].rjust(2,'0')
                    continue #Done with this column
        # Get the category from the line
        category = line[:3]
        # Split the data colums that start after the 4th character into columns of three
        data = [line[i:i+3] for i in range(4, len(line), 3)]
        
        # Process data lines
        if category == "HR ":
            # The hour that each column represents
            # Reset hours for this new station
            hours = []
            # Loop over each column
            for index, d in enumerate(data):
                # Remove whitespace from the column data
                d = d.strip()
                # The date + hour for this column
                dh = date_dict[index] + d
                # Append this date/hour to the hours column list
                hours.append(dh)
                # Usng this column index
                mos_data[station][dh] = {}
                #Defaults for sometimes missing data
                mos_data[station][dh]["TYP"] = "9"

        if category == "TMP":
            # Temperatures need special processing
            for index, hour in enumerate(hours):
                temp_int = int(data[index].strip())
                # 999 = No temp reported
                if temp_int == 999:
                    mos_data[station][hour]["TMP"] = temp_int
                else:
                    # Convert from F to C so the data matches METAR data
                    mos_data[station][hour]["TMP"] = round(((temp_int - 32) * 5 ) / 9,2)

        elif category in [ "CLD", "TYP","OBV" ]:
            # Things that are Strings
            for index, hour in enumerate(hours):
                cld = data[index].strip()
                mos_data[station][hour][category] = cld

        elif category in [ "WDR", "WSP", "POZ", "POS", "CIG", "VIS" ]:
            # Things that are integers are here
            for index, hour in enumerate(hours):
                value = int(data[index].strip())
                if category == "WDR":
                    #add a zero to wind direction
                    value = value * 10
                mos_data[station][hour][category] = value

        elif category == "P06":
            for index, hour in enumerate(hours):
                temp = data[index].strip()
                if temp == '':
                    temp  = 0
                mos_data[station][hour][category] = temp
        elif category == "T06":
            # "T06 = probability of thunderstorms/conditional probability of severe thunderstorms during the 6-hr period ending at the indicated time."
            # source: https://www.nws.noaa.gov/mdl/synop/mavcard.php#:~:text=T06%20%3D%20probability%20of%20thunderstorms%2Fconditional,ending%20at%20the%20indicated%20time.
            prob = 0
            for index, hour in enumerate(hours):
                # Cannot get index + 2 at the ned 
                if (( index % 2) == 0) and (index < (len(hours) - 1)) :
                    # On even numbers, the prob values exist in index + 1 and index + 2
                    # Calculate on even numbers, reuse calculation for the next odd number
                    prob_ts = int( data[index + 1])
                    prob_sts = int(re.sub("\D", "", data[index + 2]))
                    # user larger of TS vs STS
                    if ( prob_ts > prob_sts ):
                        prob = prob_ts
                    else:
                        prob = prob_sts

                mos_data[station][hour][category] = prob


    return mos_data


