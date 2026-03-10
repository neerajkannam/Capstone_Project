// NETWORK TRAFFIC CHART

const trafficCtx = document.getElementById('trafficChart');

new Chart(trafficCtx, {

type: 'line',

data: {

labels: ['1','2','3','4','5','6','7'],

datasets: [{

label: 'Network Traffic',

data: [12,19,8,15,22,18,30],

borderWidth:2

}]

},

options: {

responsive:true

}

});



// AI PREDICTION RESULT CHART

const predictionCtx = document.getElementById('predictionChart');

new Chart(predictionCtx, {

type: 'pie',

data: {

labels: ['Normal Traffic','Cyber Attack'],

datasets: [{

data: [70,30],

borderWidth:1

}]

}

});