// Use this script with a Fluid SSB and a Roundcube installation
// Change the URL below
function transform(inURLString) {
    inURLString = inURLString.replace('mailto:', '');
    inURLString = inURLString.replace('&amp;', '&');

    var argStr = '';
    var splits = inURLString.split('?');

    var emailAddr = null;
    var args = {};
    if (splits.length > 0) emailAddr = splits[0];
    if (splits.length > 1) argStr = splits[1];

    var outURLString = 'https://mail.example.com/?_task=mail&_action=compose&to=' + emailAddr;

    if (argStr.length > 0) outURLString += '&' + argStr;
    return outURLString;
}
