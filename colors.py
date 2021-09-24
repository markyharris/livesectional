import colorsys

# Set color to a gradient between Blue and Red based on temperature
def temp(temp,min,max):
    shift = 0
    if (min < 0):
        shift = abs(min)
    if ( min > 0 ):
        shift = 0 - min
    temp = float(temp) + shift  # Shift the scale so it starts from 0
    if ( temp < 0 ):
        temp = 0  # If temp is less than min then set to 0

    if ( temp > max + shift): #highest hue
        temp = max + shift
    # Calculate the hue between 0 (red)  and 250 (blue)
    hue = (245 - (245 * ( temp / (max + shift ) ))) / 360
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(hue,1,0.7))




