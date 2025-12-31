// JavaScript source code

let satName = "Choose satellite";
let newestTime = 0;
let oldestTime = 0;
let isLoading = false;
const TWO_HOURS = 2 * 60 * 60 * 1000;

async function ChooseSat(choice) {
    if (isLoading) return;
    isLoading = true;
    choice = choice.value;
    let placeHolder = document.getElementById("packets");
    let download = document.getElementById("openDownload");
    if (choice == "Choose satellite") {
        placeHolder.innerHTML = "";
        download.innerHTML = "";
        return 0;
    }
    const url = "/chooseSatellite/" + choice;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('HTTP error! status: ' + response.status);
        }
        const data = await response.json();
        satName = choice;
        newestTime = data.mostResent;
        oldestTime = data.lestResent;
        placeHolder.innerHTML = data.data;
        download.innerHTML = `<button class="popupButton" onclick="openPopup()"></button><div class="popup" id="popup"><div class="closeBtn" onclick="closePopup()">&times;</div><div><div id="title" class="title">Download data for ${satName}</div><p>Choose type of download:<select id="chooseDownload" class="item selectDownloadType" onchange="downloadType(this)"><option value="StartToEndTime">Start to End Time</option><option value="StartTime">Start Time</option><option value="Limit">Limit</option><option value="All"> All </option></select></p><div id="types"><p>Enter start date: <input type="datetime-local" id="start-date" name="start-date" step="1" /></p><p>Enter end date: <input type="datetime-local" id="end-date" name="end-date" step="1" /><br /></p></div><button type="submit" onclick="sendDownloadRequest()">download</button><div class="error" id="error"></div></div></div>`;
    }
    catch (error) {
        console.error('Error fetching data: ', error, message);
    }
    isLoading = false;
}

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

function checkNull(element) {
    if (element == "") { return true; }
    return false;
}

function openPopup() {
    let popup = document.getElementById("popup");
    popup.classList.toggle("open-popup");
}
function closePopup() {
    let popup = document.getElementById("popup");
    popup.classList.remove("open-popup");    
}

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
            if (startTime < "1970-01-01T00:00" || endTime < "1970-01-01T00:00") {
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
            break;
        case "Limit":
            var limit = document.getElementById("limit").value;
            if (checkNull(limit)){
                errorPlace.innerHTML = "Error: don't have limit. Need to add";
                return false;
            }
            break;
        case "All": break;
        default: return false;
    }
    return true;
}

async function downloadExcel(data, filename){
    const blob = new Blob([data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }); // a .xslx file (that the type)
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();

    // Clean up
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
}

async function sendDownloadRequest() {
    if (!checkForm()) return false;
    const choice = document.getElementById("chooseDownload").value;
    let url = `/downloadData/type=${choice}?satName=${satName}`;
    switch (choice) {
        case "StartToEndTime":
            {
                const start = Math.floor(document.getElementById("start-date").valueAsNumber / 1000); //I know for a fact it's not null
                const end = Math.floor(document.getElementById("end-date").valueAsNumber / 1000);
                url += `?start=${start}?end=${end}`;
                break;
            }
        case "StartTime":
            {
                const start = Math.floor(document.getElementById("start-date").valueAsNumber / 1000);
                url += `?start=${start}`;
                break;
            }
        case "Limit":
            {
                const limit = document.getElementById("limit").valueAsNumber;
                url += `?limit=${limit}`;
                break;
            }
        case "All":
            break;
    }
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('HTTP error! status: ' + response.status);
        }
        const rawData = await response.blob();
        const disposition = response.headers.get('Content-Disposition');
        let fileName = 'download.xlsx'; // Fallback

        if (disposition && disposition.includes('filename=')) {
            fileName = disposition.split('filename=')[1].replaceAll('"', '');
        }
        downloadExcel(rawData, fileName);
    }
    catch (error) {
        console.error('Error fetching data: ', error, message);
    }
    return true;
}

async function ScrollDown() {
    if (satName == "Choose satellite") return;
    if (isLoading) return;
    isLoading = true;
    const container = document.getElementById("packets");
    const url = "/addBottom/satName=" + satName + "?lestResent=" + oldestTime;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('HTTP error! status: ' + response.status);
        }
        const data = await response.json();
        oldestTime = data.lestResent;
        const placeHolder = document.getElementById("packets");
        container.insertAdjacentHTML('beforeend', data.data);
    }
    catch (error) {
        console.error('Error fetching data: ', error.message);
    }
    isLoading = false;
}

async function ScrollUp() {
    const container = document.getElementById("packets");
    if (satName == "Choose satellite") return;
    const url = "/addTop/satName=" + satName + "?mostResent=" + newestTime;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('HTTP error! status: ' + response.status);
        }
        const data = await response.json();
        if (data.data == "") return;
        newestTime = data.mostResent;
        const placeHolder = document.getElementById("packets");
        container.insertAdjacentHTML('afterbegin', data.data);
    }
    catch (error) {
        console.error('Error fetching data: ', error.message);
    }
} 

window.addEventListener('scroll', () => {
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
    if (scrollTop + clientHeight >= scrollHeight - 20) { ScrollDown(); }
})
setInterval(ScrollUp, TWO_HOURS);


