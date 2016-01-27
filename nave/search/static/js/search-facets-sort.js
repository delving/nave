// Let user sort the facet lists alphabetically or by hit count
function sortFacets(trigger, target, type) {
    // @target is the id associated with the list
    // @type is either on 'name' or 'count
    var theList = $('#' + target).find('ul');
    var theListItems = $.makeArray(theList.children("li"));
    if (!theList.hasClass('sorted')) {
        theListItems.sort(function (a, b) {
            var textA = $(a).data(type);
            var textB = $(b).data(type);
            if (type === 'value'){
                var textA = textA.toLowerCase();
                var textB = textB.toLowerCase();
            }
            if (textA < textB) {
                return -1;
            }
            if (textA > textB) {
                return 1;
            }
            return 0;
        });
        theList.empty();
        $.each(theListItems, function (index, item) {
            theList.append(item);
        });
        theList.addClass('sorted');
        trigger.find('span').html(trigger.data('textAscending'));
    }
    else {
        theListItems.reverse();
        theList.empty();
        $.each(theListItems, function (index, item) {
            theList.append(item);
        });
        theList.removeClass('sorted');
        trigger.find('span').html(trigger.data('textDescending'));
    }
}
