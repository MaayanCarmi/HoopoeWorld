setInterval(myTime, 1000);

function myTime() {
    var d = new Date();

    // Use toUTCString() for the date and time
    var date = d.toUTCString().split(' ')[0] + " " + d.toUTCString().split(' ')[1] + " " + d.toUTCString().split(' ')[2] + " " + d.toUTCString().split(' ')[3];
    var time = d.toUTCString().split(' ')[4];  // Just the time part

    var finalTime = date + "</br>" + time + " UTC";
    let clock = document.getElementById("clock");
    clock.innerHTML = finalTime;
    let width = window.innerWidth;
    if (width < 1300) { clock.style.fontSize = `${Math.round(width / 60)}px`; }
    else { clock.style.fontSize = `25px`; }

}