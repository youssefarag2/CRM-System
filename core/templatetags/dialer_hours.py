from django import template



register = template.Library()



@register.filter
def seconds_to_hhmmss(seconds):
    """Custom filter to convert seconds to HH:MM:SS format."""
    if not seconds:
        return '00:00:00'
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

@register.filter
def get_item_and_format(dictionary, key):
    """Custom filter to get item from dictionary by key and format seconds to HH:MM:SS."""
    value = dictionary.get(key, 0)  # Default to 0 if key is not found
    return seconds_to_hhmmss(value)



@register.filter
def get_total_payable(dictionary):
    
    value1 = dictionary.get("Available", 0)  
    value2 = dictionary.get("After Call", 0)   
    value3 = dictionary.get("On Call", 0)   
    value4 = dictionary.get("In Meeting", 0)   
    value5 = dictionary.get("Wrap Up Time", 0)    
    value6 = dictionary.get("Auto Pause", 0)   

    total_payable = value1 + value2 + value3 + value4 + value5 + value6


    return  seconds_to_hhmmss(total_payable)





