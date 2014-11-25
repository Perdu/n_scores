function redirect() {
    var by_place = "";
    var avg = "";
    var top_opt = "";
    var diff="";
    if ($("#by_place").is(':checked')) {
	by_place = "&by_place=1"
    }
    if ($("#avg").is(':checked')) {
	avg = "&avg=1"
    }
    if ($("#diff").is(':checked')) {
        diff = "&diff=1";
        avg = "";
        by_place = "";
        top_opt = "";
    }
    var topn = $('#top').val();
    if (topn < 20)
        top_opt = "&top=" + topn;
    this.location='/level?level=' + $('#l').val() + by_place + avg + top_opt + diff;
    return false;
}

function redirect_player() {
    this.location='/player?pseudo=' + $('#player').val();
    return false;
}
