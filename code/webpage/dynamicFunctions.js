// JavaScript source code
let satName = "";
let newestTime = 0;
let oldestTime = 0;

function ChooseSat(choice) {
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
        console.error('Error fetching data:', error);
    }
}

//need to do a function of scroll down

//also when you are up.