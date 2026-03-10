const ctx = document.getElementById('resultChart');

new Chart(ctx,{
    type:'bar',
    data:{
        labels:['AI Detection'],
        datasets:[{
            label:'Confidence Score',
            data:[85],
            backgroundColor:['red']
        }]
    },
    options:{
        scales:{
            y:{
                beginAtZero:true,
                max:100
            }
        }
    }
});