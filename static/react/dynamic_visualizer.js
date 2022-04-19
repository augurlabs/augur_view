
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

  const [dataType, setDataType] = useState(null);

  function getGraphData() {
    dataType ?
    fetch('http://augur.chaoss.io/api/unstable/repo-groups/25000/' + dataType)
    .then(function(response) {
      return response.json();
    }).then(function(data) {
      console.log(data);
      var tempData = [];
      for(var i = 0; i < data.length; i ++){
        tempData.push(data[i]);
      }
      setMyData(tempData);
    }): getDefaultGraph();

  }

  function getDefaultGraph() {
    getForkData();
    getStarDataForRepoWithDates();
  }

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
    getGraphData();
  },[dataType])

  useEffect(() => {
    getGraphData();
  }, [])

  function handleChange(e) {
    setDataType(e.target.value);
    console.log(e.target.value);
    getGraphData(e.target.value);
  }
  function stringDate(dateS){
    var tempD = new Date(dateS);
    return tempD.getFullYear().toString() +"-" + tempD.getMonth() + "-" + tempD.getDate();
  }
  if( myData){
    return(

      

    //   This is for all the data
    <div style={{width:"100%", justifyContent:"center", display:"flex", "flex-flow":"column"}}>
      
        <div style={{justifyContent:"left",display:"flex"}}>
          <p>Select data to be displayed:
            <select onChange={e => handleChange(e)} id="data select" style={{margin:"10px"}}>
              <option> -- Select data -- </option>
              <option value="forks">Forks</option>
              <option value="stars">Stars</option>
            </select>
          </p>
        </div>

        <div style={{justifyContent:"space-around",display:"flex"}}>
          <p>Repository 1:
            <select id="repository_1_select" style={{margin:"10px"}}>
              <option> -- Select Repository 1 -- </option>
            </select>
          </p>
          <p>Repository 2:
            <select id="repository_2_select" style={{margin:"10px"}}>
              <option> -- Select Repository 2 -- </option>
            </select>
          </p>
        </div>
    
      <div id="graph1">
        <h1>Stars over time for {myData[0].repo_name}</h1>
          <LineChart width={750} height={500} data={myData} style={{margin:"100px auto"}} >

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
          <LineChart width={750} height={500} data={forkData} style={{margin:"100px auto"}} >

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