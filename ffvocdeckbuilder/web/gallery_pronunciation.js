function setFfvdbPronunciation(n) {
    pycmd("ffvdb:pronunciation:set." + n);
}

function playPronunciation(n) {
    pycmd("ffvdb:pronunciation:play." + n);
}
