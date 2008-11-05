// Removes leading and ending whitespaces, nbsps
function trim(str) {
    return str.replace(/(^[\s\xA0]+|[\s\xA0]+$)/g, '');
}
