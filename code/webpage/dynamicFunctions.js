let satName = "Choose satellite";
let newestTime = 0;
let oldestTime = 0;
let isLoading = false;
const TWO_HOURS = 2 * 60 * 60 * 1000; //in milisecond.

/**
 * onchange function that when we change a satellite it will ask for the most current data of this sat.
 * also change the global varibles accordingly, and open and close the option to download as excel.
 * @param {string} choice - which sat or deafult
 * @returns null
 */
async function ChooseSat(choice) {
    if (isLoading) return;
    isLoading = true; //so we will not go down or up and at the same time change. (will be bad)
    choice = choice.value;
    let placeHolder = document.getElementById("packets"); //where at the end the packets will go to
    let download = document.getElementById("openDownload"); //for the option to download
    if (choice == "Choose satellite") { //if none of the satellites are choosen
        placeHolder.innerHTML = "";
        download.innerHTML = "";
        return 0;
    }
    const url = "/chooseSatellite/" + choice;
    try {
        const response = await fetch(url); //try to get data from server
        if (!response.ok) {
            throw new Error('HTTP error! status: ' + response.status);
        }
        const data = await response.json(); //get json from that.
        //put global params
        satName = choice;
        newestTime = data.mostResent;
        oldestTime = data.lestResent;
        placeHolder.innerHTML = data.data; //place the packets in place
        //add the option for download
        download.innerHTML = `<button class="popupButton" onclick="openPopup()"></button><div class="popup" id="popup"><div class="closeBtn" onclick="closePopup()">&times;</div><div><div id="title" class="title">Download data for ${satName}</div><p>Choose type of download:<select id="chooseDownload" class="item selectDownloadType" onchange="downloadType(this)"><option value="StartToEndTime">Start to End Time</option><option value="StartTime">Start Time</option><option value="Limit">Limit</option><option value="All"> All </option></select></p><div id="types"><p>Enter start date: <input type="datetime-local" id="start-date" name="start-date" step="1" /></p><p>Enter end date: <input type="datetime-local" id="end-date" name="end-date" step="1" /><br /></p></div><button type="submit" onclick="sendDownloadRequest()">download</button><div class="error" id="error"></div></div></div>`;
    }
    catch (error) {
        console.error('Error fetching data: ', error, message);
    }
    isLoading = false;
}

/**
 * according to choice add the correct filter.
 * @param {string} choice - choice of which download filter to use.
 */
function downloadType(choice) {
    choice = choice.value;
    let placeHolder = document.getElementById("types");
    switch (choice) {
        case "StartToEndTime":
            placeHolder.innerHTML = "<p>Enter start date: <input type=\"datetime-local\" id=\"start-date\" name=\"start-date\" step=\"1\" /></p><p>Enter end date: <input type=\"datetime-local\" id=\"end-date\" name=\"end-date\" step=\"1\" /></p>";
            break;
        case "StartTime":
            placeHolder.innerHTML = "<p>Enter start date: <input type=\"datetime-local\" id=\"start-date\" name=\"start-date\" step=\"1\" /></p>";
            break;
        case "Limit":
            placeHolder.innerHTML = "<p>Amount of packets: <input type=\"number\" id=\"limit\" name=\"limit\" placeholder=\"amount of packets\" min=\"1\"/></p>";
            break;
        case "All":
            placeHolder.innerHTML = "";
            break;
    }
}

/**
 * check if we didn't enter stuff.
 * @param {string} element
 * @returns true on empty false on full.
 */
function checkNull(element) {
    if (element == "") { return true; }
    return false;
}

/**
 * both open and close but add to the button. (close just in case they don't want to go up in the website).
 */
function openPopup() {
    let popup = document.getElementById("popup");
    popup.classList.toggle("open-popup"); //if have remove else add.
}
/**
 * close the popup. (for the x button)
 */
function closePopup() {
    let popup = document.getElementById("popup");
    popup.classList.remove("open-popup");    
}

/**
 * check if the form is valid and if not write an error msg.
 * @returns false on error, true otherwise.
 */
function checkForm() {
    const choice = document.getElementById("chooseDownload").value;
    let errorPlace = document.getElementById("error");
    errorPlace.innerHTML = "";
    switch (choice) {
        case "StartToEndTime":
            var startTime = document.getElementById("start-date").value;
            var endTime = document.getElementById("end-date").value;
            if (checkNull(startTime) || checkNull(endTime)) {
                errorPlace.innerHTML = "Error: don't have at lest one time. Need to add";
                return false;
            }
            if (startTime > endTime) {
                errorPlace.innerHTML = "Error: start time is bigger then end time";
                return false;
            }
            if (startTime < "1970-01-01T00:00" || endTime < "1970-01-01T00:00") { //because of time_unix
                errorPlace.innerHTML = "Error: time need to be after 1.1.1970 00:00";
                return false;
            }
            break;
        case "StartTime":
            var startTime = document.getElementById("start-date").value;
            if (checkNull(startTime)) {
                errorPlace.innerHTML = "Error: don't have at lest start time. Need to add";
                return false;
            }
            if (startTime < "1970-01-01T00:00") { //because of time_unix
                errorPlace.innerHTML = "Error: time need to be after 1.1.1970 00:00";
                return false;
            }
            break;
        case "Limit":
            var limit = document.getElementById("limit").value;
            if (checkNull(limit)){
                errorPlace.innerHTML = "Error: don't have limit. Need to add";
                return false;
            }
            break;
        case "All": break;
        default: return false; //a not known place.
    }
    return true;
}

/**
 * send and get the request for download .xslx
 * @returns null
 */
async function sendDownloadRequest() {
    if (!checkForm()) return; //if not valid
    const choice = document.getElementById("chooseDownload").value;
    let url = `/downloadData/?type=${choice}&satName=${satName}`; //the start of the url that is right to all types.
    switch (choice) {
        case "StartToEndTime":
            {
                const start = Math.floor(document.getElementById("start-date").valueAsNumber / 1000); //I know for a fact it's not null, and time
                const end = Math.floor(document.getElementById("end-date").valueAsNumber / 1000);
                url += `&start=${start}&end=${end}`; //add the other params according to protocol.
                break;
            }
        case "StartTime":
            {
                const start = Math.floor(document.getElementById("start-date").valueAsNumber / 1000);
                url += `&start=${start}`;
                break;
            }
        case "Limit":
            {
                const limit = document.getElementById("limit").valueAsNumber; //get limit as a number
                url += `&limit=${limit}`; ///add the param according to protocol.
                break;
            }
        case "All":
            break;
    }
    window.location.href = url; //get from server the file by the url.
}

/**
 * make the website look like it has an infinite scrolling down. 
 * this is what it send.
 * @returns null
 */
async function ScrollDown() {
    if (satName == "Choose satellite") return;
    if (isLoading) return; //same check as chooseSat
    isLoading = true;
    const container = document.getElementById("packets");
    const url = `/addBottom/?satName=${satName}&lestResent=${oldestTime}`; //to get the 25 packets that are just after the oldest I have.
    try {
        const response = await fetch(url);
        if (!response.ok) { //check for an error
            throw new Error('HTTP error! status: ' + response.status);
        }
        const data = await response.json();
        oldestTime = data.lestResent; //change the oldest presented time
        container.insertAdjacentHTML('beforeend', data.data); //add to the end of the div
    }
    catch (error) {
        console.error('Error fetching data: ', error.message);
    }
    isLoading = false;
}

/**
 * every two hours this function is called to make sure we have current data.
 * this is what it send.
 * @returns null
 */
async function ScrollUp() {
    const container = document.getElementById("packets");
    if (satName == "Choose satellite") return;
    const url = `/addTop/?satName=${satName}&mostResent=${newestTime}`; //to get the packets that are just before what I have.
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('HTTP error! status: ' + response.status);
        }
        const data = await response.json();
        if (data.data == "") return; //in case there is none
        newestTime = data.mostResent; //change the newest presented time
        container.insertAdjacentHTML('afterbegin', data.data); //add to the start of the div
    }
    catch (error) {
        console.error('Error fetching data: ', error.message);
    }
} 
/**
 * do the infinite scrolling.
 */
window.addEventListener('scroll', () => {
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
    if (scrollTop + clientHeight >= scrollHeight - 20) { ScrollDown(); }
})
setInterval(ScrollUp, TWO_HOURS); //up every two hours


