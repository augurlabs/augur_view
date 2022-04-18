
const {useEffect, useState} = React;
const {Line, LineChart} = Recharts;
function DynamicVisualizer(){
  const [myData, setMyData] = useState(null)
  useEffect(() => {
    fetch('http://augur.chaoss.io/api/unstable/repo-groups')
    .then(function(response) {
      return response.json();
    }).then(function(data) {
      console.log(data)
      setMyData(data);
    });
  }, [])
  if(myData){
    return(
      <div>
        {myData[0].rg_name}
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