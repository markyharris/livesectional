import colorsys

# Set color to a gradient between Blue and Red based on temperature
def temp(temp,min,max):
    shift = 0
    if (min < 0):
        shift = abs(min)
    temp = float(temp) + shift  # Shift the scale so it starts from 0
    if ( temp < 0 ):
        temp = 0  # If temp is less than min then set to 0

    if ( temp > max): #highest hue is 38c ~100f
        temp = max
    # Calculate the hue between 140(min) and 360(max)
    hue = (240 + (120 * ( temp / (max + shift ) )))/ 360
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(hue,1,1))




