from django import template

register = template.Library()


@register.filter
def numbered_pages(value, current_page, max_pages=8):
    """
    4 scenarios:
      1 - the number of pages is less than the max... just return the range untouched
      2 - the current page is within the max number, so we're going to return the range starting at page 1 and add ...
      3 - the current page is not within max_pages of the beginning, but within max_pages of the end so prepend ...
      4 - the current page is in the middle of a bunch of page numbers...
    """
    if value is not None:
        page_range = value[:]
    else:
        page_range = []
    if len(page_range) > max_pages:
        if current_page - max_pages < 0:
            new_range = page_range[0:max_pages]
            new_range.extend(['...', page_range[-1]])
        elif current_page + max_pages > len(page_range):
            new_range = ['1', '1...']
            new_range.extend(page_range[-max_pages:])
        else:
            new_range = ['1', '1...']
            new_range.extend(page_range[(current_page - (max_pages / 2)):(current_page + (max_pages / 2))])
            new_range.extend(['...', page_range[-1]])
        return new_range
    else:
        return page_range


@register.filter
def numbered_pages_elli(value):
    if value == '...' or value == '1...':
        return '&hellip;'
    return value


@register.filter
def numbered_pages_link(value, default=''):
    if value == '...':
        return default
    elif value == '1...':
        return default
    else:
        return value