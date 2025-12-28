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
    if (choice == "Choose satellite") return 0;
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
        const placeHolder = document.getElementById("packets");
        placeHolder.innerHTML = data.data;
    }
    catch (error) {
        console.error('Error fetching data: ', error, message);
    }
    isLoading = false;
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
