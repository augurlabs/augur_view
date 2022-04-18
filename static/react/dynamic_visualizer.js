
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
      setMyData(data);
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
  if( myData){
    return(
    //   This is for all the data
      <LineChart width={800} height={500} data={myData}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="date" />
      <YAxis />
      <Tooltip />
      <Legend />
      <Line type="monotone" dataKey="stars" stroke="#8884d8" />
    </LineChart>
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