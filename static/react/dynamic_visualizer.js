
const {useEffect, useState} = React;
const {Line, LineChart,CartesianGrid, XAxis, YAxis, Tooltip, Legend} = Recharts;
function formatDate(date) {
  var d = new Date(date),
    month = '' + (d.getMonth() + 1),
    day = '' + d.getDate(),
    year = d.getFullYear();

  if (month.length < 2) 
    month = '0' + month;
  if (day.length < 2) 
    day = '0' + day;

  return [year, month, day].join('-');
}
function DynamicVisualizer(){
  const [myData, setMyData] = useState(null)

  const [forkData, setForkData] = useState(null);

  function getStarDataForRepoWithDates(){
    fetch('http://augur.chaoss.io/api/unstable/repo-groups/25000/stars')
    .then(function(response) {
      return response.json();
    }).then(function(data) {
      console.log(data)
      var tempData = []
      for(var i = 0; i < data.length; i ++){
        tempData.push(data[i])
      }
      setMyData(tempData)
    });
  }
  function getForkData(){
    fetch('http://augur.chaoss.io/api/unstable/repo-groups/25000/forks')
    .then(function(response) {
      return response.json();
    }).then(function(data) {
      console.log(data)
      for(var i =0;i<data.length;i++){
        data[i].date = formatDate(data[i].date);
      }
      setForkData(data)
    });
  }




  useEffect(() => {
    // fetch('http://augur.chaoss.io/api/unstable/repos')
    // .then(function(response) {
    //   return response.json();
    // }).then(function(data) {
    //   console.log(data)
    //   setMyData(data);
    // });
    getStarDataForRepoWithDates()
    getForkData();
  }, [])
  function stringDate(dateS){
    var tempD = new Date(dateS);
    console.log(tempD.getFullYear().toString())
    return tempD.getFullYear().toString() +"-" + tempD.getMonth() + "-" + tempD.getDate();
  }
  if( myData){
    return(
    //   This is for all the data
    <div style={{width:"100%", justifyContent:"center", display:"flex", "flex-flow":"column"}}>
      <div id="graph1">
        <h1>Stars over time for {myData[0].repo_name}</h1>
          <LineChart width={1000} height={500} data={myData} style={{margin:"100px auto"}} >

            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" angle={-28} textAnchor="end" tickFormatter={(tickS) => {return stringDate(tickS)}}/>
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="stars" stroke="#8884d8" />
        </LineChart>
        </div>
        <div id="graph2">
        <h1>Forks over time for {myData[0].repo_name}</h1>
          <LineChart width={1000} height={500} data={forkData} style={{margin:"100px auto"}} >

            <CartesianGrid />
            <XAxis dataKey="date" angle={-28} textAnchor="end"/>
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="forks" stroke="#8884d8" />
        </LineChart>
        </div>
    </div>
    )
  }
  return (
    <div>

    </div>
  )
}

const domContainer = document.querySelector('.content');
const root = ReactDOM.createRoot(domContainer);
root.render(<DynamicVisualizer />);