
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

  const [firstGraph, setFirstGraph] = useState(null);

  const [secondGraph, setSecondGraph] = useState(null);
  
  const [repoNames, setRepoNames] = useState(null);

  const [firstRepoId, setFirstRepoId] = useState(null);

  const [secondRepoId, setSecondRepoId] = useState(null);

  const [dataType, setDataType] = useState(null);

  // function getStarDataForRepoWithDates(){
  //   fetch('http://augur.chaoss.io/api/unstable/repo-groups/25000/stars')
  //   .then(function(response) {
  //     return response.json();
  //   }).then(function(data) {
  //     console.log(data)
  //     var tempData = []
  //     for(var i = 0; i < data.length; i ++){
  //       tempData.push(data[i])
  //     }
  //     setMyData(tempData)
  //   });
  // }
  // function getForkData(){
  //   fetch('http://augur.chaoss.io/api/unstable/repo-groups/25000/forks')
  //   .then(function(response) {
  //     return response.json();
  //   }).then(function(data) {
  //     console.log(data)
  //     for(var i =0;i<data.length;i++){
  //       data[i].date = formatDate(data[i].date);
  //     }
  //     setForkData(data)
  //   });
  // }

  function getRepoNames(){
    fetch("http://augur.chaoss.io/api/unstable/repos").then(function(res){
      return res.json()
    }).then(function(data){
      var tempRepoNames = [];
      for(var i =0; i < data.length; i ++){
        if( data[i].repo_name != null || data[i].repo_name !== ''){
          tempRepoNames.push({"name" : data[i].repo_name, "id" : data[i].repo_id});
        }
      }
      setRepoNames(tempRepoNames)
    })
  }
  // function getFirstGraphData(){
  //   fetch("http://augur.chaoss.io/api/unstable/repos/" + firstRepoId + "/watchers-count").then(
  //     function(res){
  //       return res.json()
  //     }
  //   ).then(function(data){
  //     console.log(data)
  //   })
  //   fetch("http://augur.chaoss.io/api/unstable/repos/" + firstRepoId + "/stars-count").then(
  //     function(res){
  //       return res.json()
  //     }
  //   ).then(function(data){
  //     console.log(data)
  //   })
  //   fetch("http://augur.chaoss.io/api/unstable/repos/" + firstRepoId + "/stars-count").then(
  //     function(res){
  //       return res.json()
  //     }
  //   ).then(function(data){
  //     console.log(data)
  //   })
  // }


  useEffect(() => {
    getRepoNames()
  }, [])

  // useEffect(() => {
  //   getFirstGraphData()
  // },[firstRepoId])

  function getGraphDataForRepos(){
    if(dataType != null && firstRepoId != null && secondRepoId != null){
      fetch("http://augur.chaoss.io/api/unstable/repos/"+ firstRepoId+ "/" + dataType)
      .then(function(res){
        return res.json()
      }).then(function(data){
        console.log(data)
        if(data != null && data.length > 0){
          var tempA = []
          for(var i =0; i <data.length; i ++){
            if(i % 10 == 0){
              tempA.push(data[i])
            }
          }
          setFirstGraph(tempA)
        }
      })
      fetch("http://augur.chaoss.io/api/unstable/repos/"+ secondRepoId+"/" + dataType)
      .then(function(res){
        return res.json()
      }).then(function(data){
        if(data != null){
          var tempB = []
          for(var i =0; i <data.length; i ++){
            if(i % 10 == 0){
              tempB.push(data[i])
            }
          }
          setSecondGraph(tempB)
        }
      })
    }
  }

  useEffect(() => {
    getGraphDataForRepos()
    console.log("ran")
  }, [dataType, firstRepoId, secondRepoId])

  function handleDataChange(e) {
    setDataType(e.target.value);
    // getGraphData(e.target.value);
  }
  function stringDate(dateS){
    var tempD = new Date(dateS);
    return tempD.getFullYear().toString() +"-" + tempD.getMonth() + "-" + tempD.getDate();
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      console.log(payload[0].payload)
      return (
        <div style={{backgroundColor: "white"}}>
        { payload[0].payload ?
          <p style={{color:"black"}} className="desc">{dataType} :  {payload[0].payload[dataType]}</p>:
          <p></p>
        }
          <p style={{color:"black"}} className="label">{'Date :' + stringDate(payload[0].value)}</p>
        </div>
      );
    }
  
    return null;
  };
  if( repoNames){
    return(
    //   This is for all the data
    <div style={{width:"100%", justifyContent:"center", display:"flex", "flex-flow":"column"}}>
      <div>
      <div style={{justifyContent:"left",display:"flex"}}>
          <p>Select data to be displayed:
            <select onChange={e => handleDataChange(e)} id="data select" style={{margin:"10px"}}>
              <option> -- Select data -- </option>
              <option value="forks">Forks</option>
              <option value="stars">Stars</option>
              <option value="watchers">Watchers</option>
              <option value="code-changes">Code changes</option>
              <option value="contributors">Contributors</option>
            </select>
          </p>
        </div>

        <div style={{justifyContent:"space-around",display:"flex"}}>
          <p>Repository 1:
            <select id="repository_1_select" style={{margin:"10px"}} onChange={(e) => setFirstRepoId(e.target.value)}>
              <option> -- Select Repository 1 -- </option>
              {
                repoNames != null && repoNames.length != 0?
                repoNames.map(data =>
                  <option value={data.id}>{data.name}</option>
                ): <option></option>
              }
            </select>
          </p>
          <p>Repository 2:
            <select id="repository_2_select" style={{margin:"10px"}} onChange={(e) => setSecondRepoId(e.target.value)}>
              <option> -- Select Repository 2 -- </option>
              {
                repoNames != null && repoNames.length != 0?
                repoNames.map(data =>
                  <option value={data.id}>{data.name}</option>
                ): <option></option>
              }
            </select>
          </p>
        </div>

      </div>
      
    <div id="graphContainer" style={{width:"100%", justifyContent:"center", display:"flex", "flex-flow":"row", "justify-content":"space-around"}}>
      {firstGraph? 
      <div id="graph1">
        <h1>{dataType} over time for {firstGraph[0].repo_name}</h1>
          <LineChart width={500} height={500} data={firstGraph} style={{margin:"100px auto"}} >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" angle={-28} textAnchor="end" tickFormatter={(tickS) => {return stringDate(tickS)}}/>
            <YAxis />
            <Tooltip content={CustomTooltip} />
            <Legend />
            <Line type="monotone" dataKey={dataType == 'code-changes'? "commit_count": dataType} stroke="#8884d8" />
        </LineChart>
        </div>
        : <div></div>
      }
      {secondGraph?
        <div id="graph2">
        <h1>{dataType} over time for {secondGraph[0].repo_name}</h1>
          <LineChart width={500} height={500} data={secondGraph} style={{margin:"100px auto"}} >
            <CartesianGrid />
            <XAxis dataKey="date" angle={-28} textAnchor="end" tickFormatter={(tickS) => {return stringDate(tickS)}}/>
            <YAxis />
            <Tooltip content={CustomTooltip}/>
            <Legend />
            <Line type="monotone" dataKey={dataType == 'code-changes'? "commit_count": dataType} stroke="#8884d8" />
        </LineChart>
        </div>
        :<div></div>
      }
      <div>
        
      </div>
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