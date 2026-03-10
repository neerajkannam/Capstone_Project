var map = L.map('map').setView([20,0],2)

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
maxZoom:5
}).addTo(map)

var marker = null

const ctx = document.getElementById('trafficChart')

const chart = new Chart(ctx,{
type:'bar',
data:{
labels:['Normal','Attack'],
datasets:[{
label:'Traffic',
data:[0,0]
}]
}
})

function updateData(){

fetch('/live-data')
.then(res=>res.json())
.then(data=>{

chart.data.datasets[0].data=[data.normal,data.attack]
chart.update()

if(marker){
map.removeLayer(marker)
}

marker = L.marker([data.lat,data.lon]).addTo(map)

})

}

setInterval(updateData,2000)