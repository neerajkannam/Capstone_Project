window.onload = function(){

// ================= NETWORK TRAFFIC CHART =================

const trafficCtx = document.getElementById('trafficChart');

if(trafficCtx){

new Chart(trafficCtx,{

type:'line',

data:{
labels:['1','2','3','4','5','6','7'],

datasets:[{
label:'Network Traffic',
data:[12,19,8,15,22,18,30],
borderColor:'#00ffc8',
borderWidth:2
}]
},

options:{responsive:true}

});

}



// ================= AI PREDICTION CHART =================

const predictionCtx = document.getElementById('predictionChart');

if(predictionCtx){

new Chart(predictionCtx,{

type:'pie',

data:{
labels:['Normal Traffic','Cyber Attack'],

datasets:[{
data:[50,20],
backgroundColor:['green','red']
}]
}

});

}



// ================= WORLD ATTACK MAP =================

const mapDiv = document.getElementById("attackMap");

if(mapDiv){

var map = L.map('attackMap').setView([20,0],2);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
maxZoom:18
}).addTo(map);

var attacks = [

{source:[28.61,77.20], target:[37.77,-122.41], type:"DDoS"},
{source:[55.75,37.61], target:[40.71,-74.00], type:"Malware"},
{source:[35.68,139.69], target:[51.50,-0.12], type:"Botnet"},
{source:[39.90,116.40], target:[48.85,2.35], type:"SQL Injection"}

];

function generateAttack(){

let attack = attacks[Math.floor(Math.random()*attacks.length)];

let source = attack.source;
let target = attack.target;

L.circleMarker(source,{radius:6,color:"red"}).addTo(map);
L.circleMarker(target,{radius:6,color:"lime"}).addTo(map);

let line = L.polyline([source,target],{color:"yellow"}).addTo(map);

line.bindPopup("⚠ "+attack.type);

}

setInterval(generateAttack,3000);

}

}