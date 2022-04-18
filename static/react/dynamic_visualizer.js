
const {useEffect, useState} = React;
const {Line, LineChart,CartesianGrid, XAxis, YAxis, Tooltip, Legend} = Recharts;
function DynamicVisualizer(){
  const [myData, setMyData] = useState(null)

  function getDataForRepoWithDates(){
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
  useEffect(() => {
    // fetch('http://augur.chaoss.io/api/unstable/repos')
    // .then(function(response) {
    //   return response.json();
    // }).then(function(data) {
    //   console.log(data)
    //   setMyData(data);
    // });
    getDataForRepoWithDates()
  }, [])
  function stringDate(dateS){
    var tempD = new Date(dateS);
    console.log(tempD.getFullYear().toString())
    return tempD.getFullYear().toString() +"-" + tempD.getMonth() + "-" + tempD.getDate();
  }
  if( myData){
    return(
    //   This is for all the data
    <div style={{width:"100%", justifyContent:"center"}}>
     
        <h1>Stars over time for {myData[0].repo_name}</h1>
          <LineChart width={500} height={500} data={myData} style={{margin:"100px auto"}} >

            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tickFormatter={(tickS) => {return stringDate(tickS)}}/>
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="stars" stroke="#8884d8" />
        </LineChart>
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