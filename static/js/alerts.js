const attacks = [
"⚠ DDoS Attack Detected",
"⚠ Brute Force Login Attempt",
"⚠ Malware Traffic Detected",
"⚠ Suspicious Network Activity",
"⚠ SQL Injection Attempt",
"⚠ Botnet Command Detected"
];

function generateAlert(){

let randomAttack = attacks[Math.floor(Math.random()*attacks.length)];

let alertBox = document.getElementById("alerts");

let newAlert = document.createElement("p");

newAlert.innerText = randomAttack + " - " + new Date().toLocaleTimeString();

newAlert.style.color="red";

alertBox.prepend(newAlert);

}

setInterval(generateAlert,4000);